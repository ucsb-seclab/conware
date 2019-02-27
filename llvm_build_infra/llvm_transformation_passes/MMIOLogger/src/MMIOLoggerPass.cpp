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


using namespace llvm;

namespace Conware {


    /***
     * The main pass.
     */
    struct MMIOLoggerPass: public ModulePass {
    public:
        static char ID;

        MMIOLoggerPass() : ModulePass(ID) {
        }

        ~MMIOLoggerPass() {
        }

        Type *getStructureAccessType(Type *currType) {
            if(currType->isPointerTy()) {
                PointerType *currPtrType = dyn_cast<PointerType>(currType);
                return this->getStructureAccessType(currPtrType->getPointerElementType());
            }
            return currType;
        }

        bool processFunction(Function &currFunc) {
            for(auto &currBB: currFunc) {
                for(auto &currIns: currBB) {
                    Instruction *currInstrPtr = &currIns;
                    if(GetElementPtrInst *targetAccess = dyn_cast<GetElementPtrInst>(currInstrPtr)) {
                        Type *accessedType = targetAccess->getPointerOperandType();
                        Type *targetAccType = this->getStructureAccessType(accessedType);
                        if(targetAccType->isStructTy()) {
                            dbgs() << "[*] Target struct name:" << targetAccType->getStructName() << "\n";
                        }

                    }
                }
            }
        }


        bool runOnModule(Module &m) override {
            for(auto &currFu: m) {
                processFunction(currFu);
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