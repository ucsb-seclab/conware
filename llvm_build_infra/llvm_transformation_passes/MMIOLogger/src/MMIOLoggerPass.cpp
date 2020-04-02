//
// Created by machiry on 2/25/19.
//

//
// Created by machiry at the beginning of time.
//

#include <llvm/Pass.h>
#include <llvm/IR/Function.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/ValueSymbolTable.h>
#include <iostream>
#include <llvm/Analysis/CallGraph.h>
#include <llvm/Analysis/LoopInfo.h>
#include <llvm/Support/Debug.h>
#include <llvm/Analysis/CFGPrinter.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/IR/Module.h>
#include <llvm/Support/CommandLine.h>
#include <set>
#include "MemAccessFetcher.h"
#include "InstrumentationHelper.h"


using namespace llvm;

namespace Conware {


    /***
     * The main pass which try to instrument all the target
     * memory instructions which could read or write
     * MMIO regions.
     */
    struct MMIOLoggerPass: public FunctionPass {
    public:
        static char ID;
        static InstrumentationHelper *currInstrHelper;

        std::set<std::string> structSet;
        // ISR function list with function name and ISR number.
        std::map<std::string, unsigned> isrFunctionList = {
            {"SUPC_Handler",16},
            {"RSTC_Handler",17},
            {"RTC_Handler",18},
            {"RTT_Handler",19},
            {"WDT_Handler",20},
            {"PMC_Handler",21},
            {"EFC0_Handler",22},
            {"EFC1_Handler",23},
            {"UART_Handler",24},
            {"SMC_Handler",25},
            {"PIOA_Handler",27},
            {"PIOB_Handler",28},
            {"PIOC_Handler",29},
            {"PIOD_Handler",30},
            {"USART0_Handler",33},
            {"USART1_Handler",34},
            {"USART2_Handler",35},
            {"USART3_Handler",36},
            {"HSMCI_Handler",37},
            {"TWI0_Handler",38},
            {"TWI1_Handler",39},
            {"SPI0_Handler",40},
            {"SSC_Handler",42},
            {"TC0_Handler",43},
            {"TC1_Handler",44},
            {"TC2_Handler",45},
            {"TC3_Handler",46},
            {"TC4_Handler",47},
            {"TC5_Handler",48},
            {"TC6_Handler",49},
            {"TC7_Handler",50},
            {"TC8_Handler",51},
            {"PWM_Handler",52},
            {"ADC_Handler",53},
            {"DACC_Handler",54},
            {"DMAC_Handler",55},
            {"UOTGHS_Handler",56},
            {"TRNG_Handler",57},
            {"EMAC_Handler",58},
            {"CAN0_Handler",59},
            {"CAN1_Handler",60},
        };
        MMIOLoggerPass() : FunctionPass(ID) {
            // Add all of the peripheral structs to be instrumented
            structSet.insert("struct.Adc");
            structSet.insert("struct.Can");
            structSet.insert("struct.CanMb");
            structSet.insert("struct.Chipid");
            structSet.insert("struct.Dacc");
            structSet.insert("struct.Dmac");
            structSet.insert("struct.DmacCh_num");
            structSet.insert("struct.Efc");
            structSet.insert("struct.Emac");
            structSet.insert("struct.EmacSa");
            structSet.insert("struct.Gpbr");
            structSet.insert("struct.Hsmci");
            structSet.insert("struct.Matrix");
            structSet.insert("struct.Pdc");
            structSet.insert("struct.Pio");
            structSet.insert("struct.Pmc");
            structSet.insert("struct.Pwm");
            structSet.insert("struct.PwmCmp");
            structSet.insert("struct.PwmCh_num");
            structSet.insert("struct.Rstc");
            structSet.insert("struct.Rtc");
            structSet.insert("struct.Rtt");
            structSet.insert("struct.Sdramc");
            structSet.insert("struct.Smc");
            structSet.insert("struct.SmcCs_number");
            structSet.insert("struct.Spi");
            structSet.insert("struct.Ssc");
            structSet.insert("struct.Supc");
            structSet.insert("struct.Tc");
            structSet.insert("struct.TcChannel");
            structSet.insert("struct.Trng");
            structSet.insert("struct.Twi");
            structSet.insert("struct.Uart");
            structSet.insert("struct.Uotghs");
            structSet.insert("struct.UotghsHstdma");
            structSet.insert("struct.UotghsDevdma");
            structSet.insert("struct.Usart");
            structSet.insert("struct.Wdt");
        }

        ~MMIOLoggerPass() {
        }

        /***
         * Get the target type embedded into the current type.
         * @param currType Type whose embedded type needs to be fetched.
         * @return Target embedded type.
         */
        Type *getStructureAccessType(Type *currType) {
            if(currType->isPointerTy()) {
                PointerType *currPtrType = dyn_cast<PointerType>(currType);
                return this->getStructureAccessType(currPtrType->getPointerElementType());
            }
            return currType;
        }

        bool isAlreadyProcessed(std::set<Value*> &processedInstructions, Value *currInstr) {
            return processedInstructions.find(currInstr) != processedInstructions.end();
        }

        /***
         * Process the current function.
         * @param currFunc Target function to process.
         * @return True if the function is modified.
         */
        /*bool processFunction(Function &currFunc) {
            bool retVal = false;
            unsigned totalLoadsInstrumented = 0;
            unsigned totalStoresInstrumented = 0;
            for(auto &currBB: currFunc) {
                for(auto &currIns: currBB) {
                    Instruction *currInstrPtr = &currIns;
                    if(GetElementPtrInst *targetAccess = dyn_cast<GetElementPtrInst>(currInstrPtr)) {
                        Type *accessedType = targetAccess->getPointerOperandType();
                        Type *targetAccType = this->getStructureAccessType(accessedType);
                        if(targetAccType->isStructTy() && targetAccType->getStructName().str() == "struct.Pio") {
                            std::set<Instruction*> targetMemInstrs;
                            targetMemInstrs.clear();
                            // get all the load and store instructions that could use this.
                            MemAccessFetcher::getTargetMemAccess(targetAccess, targetMemInstrs);
                            // these are the instructions that need to be instrumented.
                            for(auto curI: targetMemInstrs) {
                                if(dyn_cast<LoadInst>(curI) != nullptr) {
                                    this->currInstrHelper->instrumentLoad(dyn_cast<LoadInst>(curI));
                                    totalLoadsInstrumented++;
                                }
                                if(dyn_cast<StoreInst>(curI) != nullptr) {
                                    this->currInstrHelper->instrumentStore(dyn_cast<StoreInst>(curI));
                                    totalStoresInstrumented++;
                                }
                                retVal = true;
                            }
                        }

                    }
                }
            }

            dbgs() << "[*]  Function:" << currFunc.getName() << ", Num Loads Instrumented:"
                   << totalLoadsInstrumented << ", Num Stores Instrumented:"
                   << totalStoresInstrumented << "\n";

            return retVal;
        }*/

        bool runOnFunction(Function &currFunc) override {
            bool retVal = false;
            std::set<Value*> processedInstructions;
#ifdef ONLYSANITY
            return retVal;
#endif

            unsigned totalLoadsInstrumented = 0;
            unsigned totalStoresInstrumented = 0;
            processedInstructions.clear();

            if (MMIOLoggerPass::currInstrHelper == nullptr) {
                MMIOLoggerPass::currInstrHelper = new InstrumentationHelper(*currFunc.getParent());
            }

            if(currFunc.hasName() && currFunc.getName() == "delay" || true) {
                for (auto &currBB: currFunc) {
                    for (auto &currIns: currBB) {
                        Instruction *currInstrPtr = &currIns;
                        if(isAlreadyProcessed(processedInstructions, currInstrPtr)) {
                            continue;
                        }
                        if (GetElementPtrInst *targetAccess = dyn_cast<GetElementPtrInst>(currInstrPtr)) {
                            Type *accessedType = targetAccess->getPointerOperandType();
                            Type *targetAccType = this->getStructureAccessType(accessedType);

                            // Is this one of the structures that maps to a peripheral?
                            if (targetAccType->isStructTy() &&
                                    structSet.find(targetAccType->getStructName().str()) != structSet.end()) {
                                std::set<Instruction *> targetMemInstrs;
                                targetMemInstrs.clear();
                                // get all the load and store instructions that could use this.
                                MemAccessFetcher::getTargetMemAccess(targetAccess, targetMemInstrs);
                                // these are the instructions that need to be instrumented.
                                for (auto curI: targetMemInstrs) {
                                    if(isAlreadyProcessed(processedInstructions, curI)) {
                                        continue;
                                    }
                                    if (dyn_cast<LoadInst>(curI) != nullptr) {
                                        processedInstructions.insert(dyn_cast<LoadInst>(curI));
                                        this->currInstrHelper->instrumentLoad(dyn_cast<LoadInst>(curI));
                                        totalLoadsInstrumented++;
                                    }
                                    if (dyn_cast<StoreInst>(curI) != nullptr) {
                                        processedInstructions.insert(dyn_cast<StoreInst>(curI));
                                        this->currInstrHelper->instrumentStore(dyn_cast<StoreInst>(curI));
                                        totalStoresInstrumented++;
                                    }
                                    retVal = true;
                                }
                            }

                        } else {
                            LoadInst *currLDInstr = dyn_cast<LoadInst>(currInstrPtr);
                            if (currLDInstr != nullptr &&
                                MemAccessFetcher::hasConstantOperand(currLDInstr->getPointerOperand())) {
                                processedInstructions.insert(currLDInstr);
                                this->currInstrHelper->instrumentLoad(currLDInstr);
                                totalLoadsInstrumented++;
                            }

                            StoreInst *currStInstr = dyn_cast<StoreInst>(currInstrPtr);

                            if (currStInstr != nullptr &&
                                MemAccessFetcher::hasConstantOperand(currStInstr->getPointerOperand())) {
                                processedInstructions.insert(currStInstr);
                                this->currInstrHelper->instrumentStore(currStInstr);
                                totalStoresInstrumented++;
                            }
//                            this->currInstrHelper->instrumentCommonInstr(currInstrPtr);
//                            return true;
                        }
                    }
                }

                dbgs() << "[*]  Function:" << currFunc.getName() << ", Num Loads Instrumented:"
                       << totalLoadsInstrumented << ", Num Stores Instrumented:"
                       << totalStoresInstrumented << "\n";
            }

            return retVal;
        }

        /*void getAnalysisUsage(AnalysisUsage &AU) const override {
            AU.addRequired<CallGraphWrapperPass>();
            AU.addRequired<LoopInfoWrapperPass>();
        }*/

    };

    char MMIOLoggerPass::ID = 0;
    InstrumentationHelper *MMIOLoggerPass::currInstrHelper = nullptr;
    static void registerSkeletonPass(const PassManagerBuilder &,
                                     legacy::PassManagerBase &PM) {
        PM.add(new MMIOLoggerPass());
    }
    static RegisterStandardPasses
            RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                           registerSkeletonPass);

    static RegisterPass<MMIOLoggerPass> x("logmmio", "MMIO Logger - Log all reads and writes to MMIO.", false, false);
}
