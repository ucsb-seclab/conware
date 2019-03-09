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

        MMIOLoggerPass() : FunctionPass(ID) {
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
#ifdef ONLYSANITY
            return retVal;
#endif

            unsigned totalLoadsInstrumented = 0;
            unsigned totalStoresInstrumented = 0;

            if (MMIOLoggerPass::currInstrHelper == nullptr) {
                MMIOLoggerPass::currInstrHelper = new InstrumentationHelper(*currFunc.getParent());
            }

            if(currFunc.hasName() && currFunc.getName() == "delay") {
                for (auto &currBB: currFunc) {
                    for (auto &currIns: currBB) {
                        Instruction *currInstrPtr = &currIns;
                        if (GetElementPtrInst *targetAccess = dyn_cast<GetElementPtrInst>(currInstrPtr)) {
                            Type *accessedType = targetAccess->getPointerOperandType();
                            Type *targetAccType = this->getStructureAccessType(accessedType);
                            if (targetAccType->isStructTy() && targetAccType->getStructName().str() == "struct.Pio") {
                                std::set<Instruction *> targetMemInstrs;
                                targetMemInstrs.clear();
                                // get all the load and store instructions that could use this.
                                MemAccessFetcher::getTargetMemAccess(targetAccess, targetMemInstrs);
                                // these are the instructions that need to be instrumented.
                                for (auto curI: targetMemInstrs) {
                                    if (dyn_cast<LoadInst>(curI) != nullptr) {
                                        this->currInstrHelper->instrumentLoad(dyn_cast<LoadInst>(curI));
                                        totalLoadsInstrumented++;
                                    }
                                    if (dyn_cast<StoreInst>(curI) != nullptr) {
                                        this->currInstrHelper->instrumentStore(dyn_cast<StoreInst>(curI));
                                        totalStoresInstrumented++;
                                    }
                                    retVal = true;
                                }
                            }

                        } else {
                            this->currInstrHelper->instrumentCommonInstr(currInstrPtr);
                            return true;
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