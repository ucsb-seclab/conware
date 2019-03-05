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

Value* InstrumentationHelper::getReadPrintString() {
    if(this->readStr == nullptr) {
        Constant *strConstant = ConstantDataArray::getString(this->targetCtx, "Read: %d from MMIO Address: %p\n");
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
        Constant *strConstant = ConstantDataArray::getString(this->targetCtx, "Wrote: %d to MMIO Address: %p\n");
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

    // set the insertion point to be after the load instruction.
    auto targetInsertPoint = targetInstr->getIterator();
    targetInsertPoint++;
    IRBuilder<> builder(&(*targetInsertPoint));

    // get the printf function.
    Function *targetPrintFunc = this->getPrintfFunction();

    // get the arguments for the function.
    Value *formatString = this->getReadPrintString();
    Value *address = targetInstr->getPointerOperand();
    Value *targetValue = targetInstr;

    // insert the call.
    builder.CreateCall(targetPrintFunc, {formatString, address, targetValue});
}

bool InstrumentationHelper::instrumentStore(StoreInst *targetInstr) {
    // set the insertion point to be after the store instruction.
    auto targetInsertPoint = targetInstr->getIterator();
    targetInsertPoint++;
    IRBuilder<> builder(&(*targetInsertPoint));

    // get the printf function.
    Function *targetPrintFunc = this->getPrintfFunction();

    // get the arguments for the function.
    Value *formatString = this->getWritePrintString();
    Value *address = targetInstr->getPointerOperand();
    Value *targetValue = targetInstr->getValueOperand();

    // insert the call.
    builder.CreateCall(targetPrintFunc, {formatString, address, targetValue});
}