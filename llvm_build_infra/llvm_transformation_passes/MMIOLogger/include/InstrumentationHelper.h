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
#include <llvm/IR/IRBuilder.h>
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
        Function *targetLogFunction;
        Function *targetInterruptLogFunction;

        /***
         * Get pointer to the print function that should be called.
         * @return Pointer to the print function.
         */
        Function* getPrintfFunction();
        Function* getLogFunction();
        Function* getInterruptLogFunction();

        /***
         * Get the format string to be used to print reads to the MMIO regions.
         * @return Pointer to the format string value.
         */
        Value* getReadPrintString();

        /***
         * Get the format string to be used to print write to the MMIO regions.
         * @return Pointer to the format string value.
         */
        Value* getWritePrintString();

        /***
         * Create a cast from pointer to void* and return the void* value.
         * @param targetBuilder IRBuilder to use.
         * @param pointerOp Pointer operand to cast.
         * @return Casted void*
         */
        Value* createPointerToVoidPtrCast(IRBuilder<> &targetBuilder, Value *pointerOp);

        /***
         * Create a cast from the given value to unsigned int.
         * @param targetBuilder IRBuilder to use.
         * @param valueOp Value to cast.
         * @return Casted Value
         */
        Value* createValueToUnsignedIntCast(IRBuilder<> &targetBuilder, Value *valueOp);

    public:
        InstrumentationHelper(Module &currMod):
        targetModule(currMod),
        targetCtx(currMod.getContext()) {
            this->readStr = nullptr;
            this->writeStr = nullptr;
            this->targetPrintFunction = nullptr;
            this->targetLogFunction = nullptr;
            this->targetInterruptLogFunction = nullptr;

        }

        virtual ~InstrumentationHelper() { }

        /***
         * Instrument the provided load instruction by calling printf on the loaded value.
         * @param targetInstr Instruction to be instrumented.
         * @return True if everything is fine.
         */
        bool instrumentLoad(LoadInst *targetInstr);

        /***
         * Instrument the provided store instruction by calling printf on the stored value.
         * @param targetInstr Instruction to be instrumented.
         * @return True if everything is fine.
         */
        bool instrumentStore(StoreInst *targetInstr);

        /***
         * Instrument the interrupt handler function to insert the logging function at the beginning.
         *
         * @param intHandlerFunc Interrupt handler function.
         * @param intNum Interrupt number
         *
         * @return Return true if we instrument it.
         */
        bool instrumentInterruptHandler(Function *intHandlerFunc, unsigned intNum);

        bool instrumentCommonInstr(Instruction *targetInstr);


    };
}

#endif //PROJECT_INSTRUMENTATIONHELPER_H
