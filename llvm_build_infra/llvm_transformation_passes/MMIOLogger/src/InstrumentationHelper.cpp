//
// Created by machiry on 3/5/19.
//

#include "InstrumentationHelper.h"
#include <llvm/IR/TypeBuilder.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/IRBuilder.h>

using namespace Conware;

Function* InstrumentationHelper::getPrintfFunction() {
    if(this->targetPrintFunction == nullptr) {
        FunctionType *printf_type =
                TypeBuilder<int(char *, ...), false>::get(this->targetCtx);

        Function *func = cast<Function>(this->targetModule.getOrInsertFunction("iprintf", printf_type));

        func->setCallingConv(CallingConv::ARM_AAPCS);

        this->targetPrintFunction = func;
    }
    return this->targetPrintFunction;
}

Function* InstrumentationHelper::getLogFunction() {
    if(this->targetLogFunction == nullptr) {
        FunctionType *conware_log_type =
                TypeBuilder<int(int *, int, int), false>::get(this->targetCtx);

        Function *func = cast<Function>(this->targetModule.getOrInsertFunction("conware_log", conware_log_type));

        func->setCallingConv(CallingConv::ARM_AAPCS);

        this->targetLogFunction = func;
    }
    return this->targetLogFunction;
}

Value* InstrumentationHelper::getReadPrintString() {
    if(this->readStr == nullptr) {
        Constant *strConstant = ConstantDataArray::getString(this->targetCtx, "Read: from MMIO Address");
        GlobalVariable *GVStr =
                new GlobalVariable(this->targetModule, strConstant->getType(), true,
                                   GlobalValue::InternalLinkage, strConstant);
        Constant *zero = Constant::getNullValue(IntegerType::getInt32Ty(this->targetCtx));
        Constant *indices[] = {zero, zero};
        Constant *strVal = ConstantExpr::getGetElementPtr(strConstant->getType(), GVStr, indices, true);
        this->readStr = strVal;
    }
    return this->readStr;
}

Value* InstrumentationHelper::getWritePrintString() {
    if(this->writeStr == nullptr) {
        Constant *strConstant = ConstantDataArray::getString(this->targetCtx, "Wrote: to MMIO Address");
        GlobalVariable *GVStr =
                new GlobalVariable(this->targetModule, strConstant->getType(), true,
                                   GlobalValue::InternalLinkage, strConstant);
        Constant *zero = Constant::getNullValue(IntegerType::getInt32Ty(this->targetCtx));
        Constant *indices[] = {zero, zero};
        Constant *strVal = ConstantExpr::getGetElementPtr(strConstant->getType(), GVStr, indices, true);
        this->writeStr = strVal;
    }
    return this->writeStr;
}

bool InstrumentationHelper::instrumentLoad(LoadInst *targetInstr) {
    bool retVal = true;

    try {
        // set the insertion point to be after the load instruction.
        auto targetInsertPoint = targetInstr->getIterator();
        targetInsertPoint++;
        IRBuilder<> builder(&(*targetInsertPoint));

        // get the log function
        Function *targetLogFunction = this->getLogFunction();

        // get the arguments for the function.
        Value *address = targetInstr->getPointerOperand();
        Value *targetValue = targetInstr;

//        ConstantInt *readValue = ConstantInt::get(IntegerType::getInt32Ty(this->targetCtx), 1);
        Constant *readValue = Constant::getNullValue(IntegerType::getInt32Ty(this->targetCtx));
        builder.CreateCall(targetLogFunction, {address, targetValue, readValue});
    } catch (const std::exception& e) {
        dbgs() << "[?] Error occurred while trying to instrument load instruction:" << e.what() << "\n";
        retVal = false;
    }
    return retVal;
}

bool InstrumentationHelper::instrumentStore(StoreInst *targetInstr) {
    bool retVal = true;
    try {
        // set the insertion point to be after the store instruction.
        auto targetInsertPoint = targetInstr->getIterator();
        targetInsertPoint++;
        IRBuilder<> builder(&(*targetInsertPoint));

        // get the log function
        Function *targetLogFunction = this->getLogFunction();

        // get the arguments for the function.
        Value *address = targetInstr->getPointerOperand();
        Value *targetValue = targetInstr->getValueOperand();

        ConstantInt *writeValue = ConstantInt::get(IntegerType::getInt32Ty(this->targetCtx), 1);
//        Constant *zero = Constant::getNullValue(IntegerType::getInt32Ty(this->targetCtx));
        builder.CreateCall(targetLogFunction, {address, targetValue, writeValue});
    } catch (const std::exception& e) {
        dbgs() << "[?] Error occurred while trying to instrument store instruction:" << e.what() << "\n";
        retVal = false;
    }
    return retVal;

}

bool InstrumentationHelper::instrumentCommonInstr(Instruction *targetInstr) {
    bool retVal = true;
    try {
        // set the insertion point to be after the store instruction.
        auto targetInsertPoint = targetInstr->getIterator();
        targetInsertPoint++;
        IRBuilder<> builder(targetInstr);

        // get the log function
        Function *targetLogFunction = this->getLogFunction();

//        builder.CreateCall(targetPrintFunc, {formatString});
        Constant *zero = Constant::getNullValue(IntegerType::getInt32Ty(this->targetCtx));
        //builder.CreateCall(targetLogFunction, {zero, zero, zero});

    } catch (const std::exception& e) {
        dbgs() << "[?] Error occurred while trying to instrument store instruction:" << e.what() << "\n";
        retVal = false;
    }
    return retVal;
}
