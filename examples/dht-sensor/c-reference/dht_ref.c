/*
 * Pure-C DHT11 reference for ATmega328P @ 16 MHz.
 *
 * Faithful equivalent of examples/dht-sensor (MicroPython style) for a fair flash
 * comparison against the PyMCU build:
 *   - DHT11 data on D2 (PD2), LED on D13 (PB5)
 *   - UART0 @ 115200 (U2X), prints "DHT11 ready" / "H: xx  T: xx" / "read error"
 *   - same single-wire 40-bit protocol and 2 s cadence
 *
 * Build:  avr-gcc -Os -mmcu=atmega328p -DF_CPU=16000000UL dht_ref.c -o dht_ref.elf
 */
#include <avr/io.h>
#include <util/delay.h>
#include <stdint.h>

#define DHT_BIT  2   /* PD2 = D2 */
#define LED_BIT  5   /* PB5 = D13 */

static void uart_init(void)
{
    UBRR0H = 0;
    UBRR0L = 16;                              /* 115200 @ 16 MHz with U2X */
    UCSR0A = (1 << U2X0);
    UCSR0B = (1 << TXEN0);
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00);
}

static void uart_putc(uint8_t c)
{
    while (!(UCSR0A & (1 << UDRE0)))
        ;
    UDR0 = c;
}

static void uart_puts(const char *s)
{
    while (*s)
        uart_putc(*s++);
}

static void uart_putu8(uint8_t v)
{
    if (v >= 100) {
        uart_putc('0' + v / 100);
        v %= 100;
        uart_putc('0' + v / 10);
        uart_putc('0' + v % 10);
    } else if (v >= 10) {
        uart_putc('0' + v / 10);
        uart_putc('0' + v % 10);
    } else {
        uart_putc('0' + v);
    }
}

/* Spin while PD2 stays at `level`, up to `timeout` iterations.
   Returns the loop count, or -1 on timeout (mirrors time_pulse_us). */
static int16_t pulse(uint8_t level, uint16_t timeout)
{
    uint16_t count = 0;
    while (((PIND >> DHT_BIT) & 1) == level) {
        if (++count >= timeout)
            return -1;
    }
    return count;
}

static uint8_t g_hum, g_temp;

static uint8_t dht_read(void)
{
    uint8_t data[5] = { 0, 0, 0, 0, 0 };

    /* Start: drive low >= 18 ms, pull high ~30 us, release to input (pull-up). */
    DDRD  |= (1 << DHT_BIT);
    PORTD &= ~(1 << DHT_BIT);
    _delay_ms(18);
    PORTD |= (1 << DHT_BIT);
    _delay_us(30);
    DDRD  &= ~(1 << DHT_BIT);

    /* ACK: sensor pulls low ~80 us then high ~80 us. */
    if (pulse(0, 1000) < 0)
        return 0;
    if (pulse(1, 1000) < 0)
        return 0;

    for (uint8_t i = 0; i < 40; i++) {
        if (pulse(0, 1000) < 0)         /* ~50 us bit-start low */
            return 0;
        int16_t hi = pulse(1, 1000);    /* high duration decides the bit */
        if (hi < 0)
            return 0;
        data[i >> 3] <<= 1;
        if (hi > 40)
            data[i >> 3] |= 1;
    }

    if (((uint8_t)(data[0] + data[1] + data[2] + data[3])) != data[4])
        return 0;

    g_hum  = data[0];
    g_temp = data[2];
    return 1;
}

int main(void)
{
    DDRB |= (1 << LED_BIT);
    uart_init();
    uart_puts("DHT11 ready\n");

    for (;;) {
        if (!dht_read()) {
            uart_puts("read error\n");
            PORTB &= ~(1 << LED_BIT);
        } else {
            uart_puts("H: ");
            uart_putu8(g_hum);
            uart_puts("  T: ");
            uart_putu8(g_temp);
            uart_putc('\n');
            PORTB |= (1 << LED_BIT);
            _delay_ms(100);
            PORTB &= ~(1 << LED_BIT);
        }
        _delay_ms(2000);
    }
}
