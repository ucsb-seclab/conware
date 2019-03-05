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
    struct MMIOLoggerPass: public ModulePass {
    public:
        static char ID;
        InstrumentationHelper *currInstrHelper;

        MMIOLoggerPass() : ModulePass(ID) {
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
        bool processFunction(Function &currFunc) {
            bool retVal = false;
            for(auto &currBB: currFunc) {
                for(auto &currIns: currBB) {
                    Instruction *currInstrPtr = &currIns;
                    if(GetElementPtrInst *targetAccess = dyn_cast<GetElementPtrInst>(currInstrPtr)) {
                        Type *accessedType = targetAccess->getPointerOperandType();
                        Type *targetAccType = this->getStructureAccessType(accessedType);
                        if(targetAccType->isStructTy()) {
                            dbgs() << "[*] Target struct name:" << targetAccType->getStructName() << "\n";
                            std::set<Instruction*> targetMemInstrs;
                            targetMemInstrs.clear();
                            // get all the load and store instructions that could use this.
                            MemAccessFetcher::getTargetMemAccess(targetAccess, targetMemInstrs);
                            // these are the instructions that need to be instrumented.
                            for(auto curI: targetMemInstrs) {
                                dbgs() << "Got Mem Instruction:" << *curI << "\n";
                                /*if(dyn_cast<LoadInst>(curI) != nullptr) {
                                    this->currInstrHelper->instrumentLoad(dyn_cast<LoadInst>(curI));
                                }*/
                                if(dyn_cast<StoreInst>(curI) != nullptr) {
                                    this->currInstrHelper->instrumentStore(dyn_cast<StoreInst>(curI));
                                }
                                retVal = true;
                            }
                        }

                    }
                }
            }

            return retVal;
        }


        bool runOnModule(Module &m) override {
            bool retVal = false;
            currInstrHelper = new InstrumentationHelper(m);
            for(auto &currFu: m) {
                retVal = processFunction(currFu) || retVal;
            }
            return true;
        }

        void getAnalysisUsage(AnalysisUsage &AU) const override {
            AU.addRequired<CallGraphWrapperPass>();
            AU.addRequired<LoopInfoWrapperPass>();
        }

    };

    char MMIOLoggerPass::ID = 0;
    static RegisterPass<MMIOLoggerPass> x("logmmio", "MMIO Logger - Log all reads and writes to MMIO.", false, false);
}