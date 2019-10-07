# Conware
Conware's goal is to automatically model hardware peripherals in software for emulation.

The overall arhitecture is as follows:


[Arduino]+[Peripheral] + [LLVM Pass](llvm-transformation-pass/) --> [Log File (TSV)] --> `pretender-model-generate` --> `pretender-model-optimize` --> `pretender-emulate`

The arduino code is instrumented with LLVM to record any MMIO read or write.
This code is than run on a real arduino with the real peripheral attached.
After a designated amount of time the log of all of the MMIO accesses are dumped over UART and stored in a log file.
This log file is then consummed by `pretender-model-generate`, which will generate a _.pickle_ model file which can be consummed by `pretender-emulate` and run on emulated hardware.
To optimize this model, which is the real power of conware, we execute `pretender-model-optimize`.


## Installation

1. we assume that you have [direnv](https://direnv.net/) installed, to help manage all of the environment path variables that must be set.
Please install it (`sudo apt-get install -y direnv`) and [hook it into your shell](https://direnv.net/docs/hook.htm).

2. We use LLVM and the arduino framework to build and manipulate our firmware.  To install these and setup your environment variables run (this will take a looong time...)
```bash
./install_dependencies.sh
```

3. We use a combination of Avatar^2 and Pretender to model our peripherals.  Too install both of these, we suggest using a [virtualenv](https://virtualenv.pypa.io/en/latest/).  
Once virtualenv is isntalled and *conware* environment is created, run:
```bash
./install_pretender.sh
```


## Example usage


## Directory structure


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
