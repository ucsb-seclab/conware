
#


# Notes
- [Arduino Command Line](https://github.com/arduino/Arduino/blob/master/build/shared/manpage.adoc)

We care about the Pio struct, found in `runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/CMSIS/Device/ATMEL/sam3xa/include/component/component_pio.h`
The actual pins are defined in `runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/CMSIS/Device/ATMEL/sam3xa/include/pio/pio_sam3x8e.h`


```C
/* Memory mapping of Cortex-M0 Hardware */
#define SCS_BASE            (0xE000E000UL)                            /*!< System Control Space Base Address */
#define CoreDebug_BASE      (0xE000EDF0UL)                            /*!< Core Debug Base Address           */
#define SysTick_BASE        (SCS_BASE +  0x0010UL)                    /*!< SysTick Base Address              */
#define NVIC_BASE           (SCS_BASE +  0x0100UL)                    /*!< NVIC Base Address                 */
#define SCB_BASE            (SCS_BASE +  0x0D00UL)                    /*!< System Control Block Base Address */

#define SCB                 ((SCB_Type       *)     SCB_BASE      )   /*!< SCB configuration struct           */
#define SysTick             ((SysTick_Type   *)     SysTick_BASE  )   /*!< SysTick configuration struct       */
#define NVIC                ((NVIC_Type      *)     NVIC_BASE     )   /*!< NVIC configuration struct          */
```

All of the MMIO structures are defined in `sam/system/CMSIS/Device/ATMEL/sam3xa/include/component/`
