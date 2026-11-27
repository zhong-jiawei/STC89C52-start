#include <REGX52.H>
#include "Delay.h"
#include "MatrixKey.h"
#include "LCD 1602.h"
unsigned char KeyNum;

void main()
{
	LCD_Init();
	LCD_showString(1,1,"MatrixKey:");
	while(1)
	{
		KeyNum=MatrixKey();
		if(KeyNum)
		{
			LCD_showNum(2,1,KeyNum,2);
		}
	}
}