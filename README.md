# Conware
Conware's goal is to automatically model hardware peripherals in software for emulation.

The overall arhitecture is as follows:


[Arduino]+[Peripheral] + [LLVM Pass](llvm-transformation-pass/) --> `conware-recorder` [Log File (TSV)] --> `conware-model-generate` --> `conware-model-optimize` --> `conware-emulate`

The arduino code is instrumented with LLVM to record any MMIO read or write.
This code is than run on a real arduino with the real peripheral attached.
After a designated amount of time the log of all of the MMIO accesses are dumped over UART and stored in a log file.
This log file is then consummed by `conware-model-generate`, which will generate a _.pickle_ model file which can be consummed by `conware-emulate` and run on emulated hardware.
To optimize this model, which is the real power of conware, we execute `conware-model-optimize`.


## Installation
  
  1. **Install [direnv](https://direnv.net/)**.
   
     `sudo apt-get install -y direnv`
     
     This is needed to help manage all of the environment path variables that must be set.
    
     **[Hook it into your shell](https://direnv.net/docs/hook.html)**.

  2.  We use LLVM and the arduino framework to build and manipulate our firmware.  
**To install these and setup your environment variables run:**
  
      Be patient: *This will take a looong time...* 
      If you have an expecially powerful machine, you can remove the **-l** parameter from ninja.  It is currently configured to be gentle on your machine.
    
```bash
./install_dependencies.sh
```

  This will install all of the neccessary dependencies, build LLVM, and setup your local environment properly with *direnv*
  
  3. We use of Avatar^2 (w/ OpenOCD) for our emulation framework.

      **Install this in a [virtualenv](https://virtualenv.pypa.io/en/latest/)**.  
      
For example, in fish:
```bash
vf create conware
```

Once virtualenv is installed *and* **conware environment is created**, run:


```bash
./install_avatar.sh
```

## Example usage

   1. Build and instrument the arduino firmware:
    
```bash
./rebuild_runtime.sh
```

   2. Build and instrument an arduino project:
    
```bash
./instrument_project.sh <arduino directory>
```

   For example:

```bash
./instrument_project.sh firmware/custom/blink/
```

   3. Execute the firmware log the data (saved a TSV file in the specified directory).  The device address is the filename in `/dev/` (e.g., ttyACM0)

```bash
conware-recorder -l <device address> <output directory>
```

For example,

```bash
conware-recorder -l ttyACM0 firmware/custom/blink/
```

This will result in a `recording.tsv` in the output directory specified.  Every other script assumes these default names.

Buffer size is defined in '/conware/runtime/arduino-1.8.8/portable/packages/arduino/hardware/sam/1.6.11/system/libsam/source'

4. You can then generate a model file using:

     **conware-model-generate**

For example:

  `conware-model-generate firmware/custom/blink/`

This will output a `model.pickle` file in the same directory.  This model is effectively a graph representation of the input file, but represented as a state machine and with memory reads represented as simple models (e.g., storage, pattern, or markov).  It has a lot of room for improvement (i.e., the point of this project)

5. To optimize this model, use:  [IN PROGESS]

    **conware-model-optimize**

For example:
```bash
conware-model-optimize firmware/custom/blink/model.pickle
```

6. To visualize a model we created, run:

     **conware-model-visualize**

For example:            
     
```bash
conware-model-visualize firmware/custom/blink/model.pickle
```


Or, to run on the optimized model,
```bash
conware-model-visualize firmware/custom/blink/model_optimized.pickle
```

The current version will dump PDF files, which can be opened to see the state machine. (e.g., _UART.gv.pdf_)

7. Once the model is optmized, it can be used to rehost the firmware
```bash
conware-emulate
```
For example,
```bash
conware-emulate --board-config pretender/configs/due.yaml -s firmware/custom/blink/build/blink.ino.bin  -r firmware/custom/blink -t 30
```
will run the firmware for 30 seconds in an emulator

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

# J-Link debugger

* Install [J-Link software](https://www.segger.com/products/debug-probes/j-link/tools/j-link-gdb-server/about-j-link-gdb-server/)
* Connect 4 SWD pins
* Run J-Link
```bash
$ JLinkExe
```
* Configure J-Link
```bash
si 1
speed 4000
device Cortex-M3
r
```
