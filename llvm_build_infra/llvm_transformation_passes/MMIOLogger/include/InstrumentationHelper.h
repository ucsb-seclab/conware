//
// Created by machiry on 3/5/19.
//

#ifndef PROJECT_INSTRUMENTATIONHELPER_H
#define PROJECT_INSTRUMENTATIONHELPER_H

#include <llvm/Pass.h>
#include <llvm/IR/Function.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/ValueSymbolTable.h>
#include <iostream>
#include <llvm/Analysis/CallGraph.h>
#include <llvm/Analysis/LoopInfo.h>
#include <llvm/Support/Debug.h>
#include <llvm/Analysis/CFGPrinter.h>
#include <llvm/IR/Module.h>
#include <set>

using namespace llvm;


namespace Conware {
    class InstrumentationHelper {
    private:
        LLVMContext &targetCtx;
        Module &targetModule;
        Value *readStr;
        Value *writeStr;
        Function *targetPrintFunction;

        /***
         *
         * @return
         */
        Function* getPrintfFunction();

        /***
         *
         * @return
         */
        Value* getReadPrintString();

        /***
         *
         * @return
         */
        Value* getWritePrintString();

    public:
        InstrumentationHelper(Module &currMod):
        targetModule(currMod),
        targetCtx(currMod.getContext()) {
            this->readStr = nullptr;
            this->writeStr = nullptr;
            this->targetPrintFunction = nullptr;

        }

        virtual ~InstrumentationHelper() { }

        /***
         *
         * @param targetInstr
         * @return
         */
        bool instrumentLoad(LoadInst *targetInstr);

        /***
         *
         * @param targetInstr
         * @return
         */
        bool instrumentStore(StoreInst *targetInstr);
    };
}

#endif //PROJECT_INSTRUMENTATIONHELPER_H
