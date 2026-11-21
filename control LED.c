#include <REG52.H>
sbit P3_0=P3^0;
sbit P3_1=P3^1;
unsigned char LEDnum;
void Delay(unsigned int time);
void main()
{
	P2 = ~0x01;
	while(1)
	{
		if(P3_1==0)
		{
			Delay(20);
			while(P3_1==0);
			Delay(20);
			
			LEDnum++;
			if(LEDnum>=8)
				LEDnum=0;
			P2=~(0x01<<LEDnum);
		}
		if(P3_0==0)
		{
			Delay(20);
			while(P3_0==0);
			Delay(20);
			
			if(LEDnum==0)
				LEDnum=7;
			else
				LEDnum--;
		}
	}
}
void Delay(unsigned int xms)
{
	unsigned char data i, j;
	while(xms--)
	{
			i = 2;
			j = 239;
			do
			{
				while (--j);
			} while (--i);
	}
}
