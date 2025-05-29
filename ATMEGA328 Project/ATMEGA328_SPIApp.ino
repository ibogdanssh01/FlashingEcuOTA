/*
Prepparing SPI communication with Raspberry Pi.
ATMEGA328 listens for messages according to SPI communication protocol. 
ATMEGA328 uses hardware SPI to communicate as Slave with Raspberry Pi.
Application consists in receiving a known message like "FLASH" from SPI Master and
sending an acknowledgement back to the master.
*/

#define F_CPU 1000000UL
#include <avr/io.h>
#include <util/delay.h>
#include <stdio.h>

// Below defines are found within Atmel Studio's implicit libraries. They must be included if working in Arduino IDE.
#define SCK 5
#define MISO 4
#define MOSI 3
#define SS 2

//spi_status bits defines
#define SPI_IF 7
#define SPI_RECV_S 6 // SPI Receiving String
#define SPI_RECV_SD 5 // SPI Receiving String Done
#define SPI_SEND_AS 4 // SPI Sending acknowlgedge as string. 

//Function-like macros
#define SET_BIT(mRegister, mBit) (mRegister |= (1<<mBit))
#define CLEAR_BIT(mRegister, mBit) (mRegister &= ~(1<<mBit))
#define READ_BIT(mRegister, mBit) ((mRegister & (1<<mBit)) != 0)


struct BufferWPos{
  uint8_t cells[25];
  uint8_t pos;
};

// Functions.
void init_uC();
void SPI_Init_Slave();
char SPI_Receive();
char str_compare(char *s1, char *s2);
void str_copy(char *s1, char *s2);
char str_length(char *s1);
void buff_addval(struct Buffer_pos, uint8_t val);
void SPI_Send();

struct BufferWPos SPI_recv_buffer, SPI_send_buffer;
uint8_t spi_rcv, spi_st = 0x00;
uint8_t i, pos;


int main(void)
{
  // Init struct vals.
  SPI_recv_buffer.pos = 0;
  SPI_send_buffer.pos = 0;
  // Init Port vals.
  init_uC();
  // Spi init
  SPI_Init_Slave();
  
  while(1)
  {
    _delay_us(500);
    if(READ_BIT(spi_st, SPI_IF))
    {
      if(READ_BIT(spi_st, SPI_RECV_SD))
      {
        CLEAR_BIT(spi_st, SPI_RECV_SD);
        if(str_compare(SPI_recv_buffer.cells, "FLASH"))
        {
          SPDR = 0x01;
          str_copy(SPI_send_buffer.cells, "ACK_FLASH");
          SPI_send_buffer.pos = 0;
          SET_BIT(spi_st, SPI_SEND_AS);
        }
        else
        {
          SPDR = 0x02;
        }
      }
    }
    
  } // -> while(1)
  
  return(0);
}
void init_uC()
{
  DDRB |= (1<<0);
  PORTB &= ~(1<<0);
}
void SPI_Init_Slave()          /* SPI Initialize function */
{
  DDRB &= ~((1<<MOSI)|(1<<SCK)|(1<<SS));  /* Make MOSI, SCK, SS as input pins */
  
  DDRB |= (1<<MISO);  /* Make MISO pin as output pin */

  SPSR &= !(1<<SPIF);  /*Prevent false interrupt at start. If SPIE is set and SPIF is set at start => False interrupt
                       SPIF = 0 resolves issue.*/
  sei();  //Enable Global Interrupts
  SPCR = (1<<SPIE) | (1<<SPE);      /* Enable SPI in slave mode,
                                    {CPOL, CPHA} = {0, 0} => MODE 0 (Only mode 0 is implemented by RPi Master),
                                    DORD = 0 => Big Endian (MSB is found on first cell, LSB on last cell.)*/
  
}


ISR(SPI_STC_vect)
{
  spi_rcv = SPDR;
  /* If spi_rcv is 1, Master wants to send a string. 
     If spi_rcv is 0, it means the whole string has been sent from master. */
  if(spi_rcv == 1)
  {
    SET_BIT(spi_st, SPI_RECV_S);
  }
  else if(spi_rcv == 0)
  {
    CLEAR_BIT(spi_st, SPI_RECV_S);
    buff_addval(&SPI_recv_buffer, '\0');
    SPI_recv_buffer.pos = 0;
    SET_BIT(spi_st, SPI_RECV_SD);
  }
  /* SPDR TO BUFFER -> SPI_RECV_S bit is set.
   * If master sent 1(1 is code for sending a string) then SPI_RECV_S is set and you need to store spi_rcv in 
     a buffer to later be able to process it.*/
  if(READ_BIT(spi_st, SPI_RECV_S))
  {
    if(spi_rcv != 1)
    {
      buff_addval(&SPI_recv_buffer, spi_rcv);
    }
  }

  /* BUFFER TO SPDR -> SPI_SEND_AS bit is set. 
   * If SPI_SEND_AS is set then master will receive 1(1 is code for sending a string). When master receives 1 then
     it knows it must generate SCK until it receives 0. This makes it possible for slave to send a message back.
  */
  if(READ_BIT(spi_st, SPI_SEND_AS))
  {
    if(SPI_send_buffer.cells[SPI_send_buffer.pos] != '\0')
    {
      SPDR = SPI_send_buffer.cells[SPI_send_buffer.pos];
      SPI_send_buffer.pos++;
    }
    else
    {
      SPDR = 0x00;
      CLEAR_BIT(spi_st, SPI_SEND_AS);
    }
  }
  SET_BIT(spi_st, SPI_IF);
}




void buff_addval(struct BufferWPos *b, uint8_t val)
{
    b->cells[b->pos] = val;
    b->pos++;
}

char str_compare(char *s1, char *s2)
{
  int i;
  for(i=0 ; s1[i] != '\0' ; i++)
  {
    if(s1[i] != s2[i])
    {
      return 0;
    }
  }
  if(s2[i]!='\0')
  {
      return 0;
  }
  return 1;
}

void str_copy(char *s1, char *s2)
{
  while(*s2 != '\0')
  {
    *s1=*s2;
    *s1++;
    *s2++;
  }
}
char str_length(char *s1)
{
  int i = 0;
  for(i=0; *s1 != '\0'; i++, s1++)
  {
    ;
  }
  return i;
}
