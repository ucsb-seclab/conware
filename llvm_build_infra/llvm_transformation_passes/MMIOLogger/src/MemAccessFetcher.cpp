//
// Created by machiry on 2/27/19.
//

#include "MemAccessFetcher.h"

using namespace llvm;

using namespace std;

namespace Conware {
    bool MemAccessFetcher::getTargetMemAccessRecursive(Instruction *srcInstr,
                                                       std::set<Instruction*> &visited,
                                                       std::set<Instruction*> &targetMemAccesses) {
        bool currVal = false;
        if(visited.find(srcInstr) == visited.end()) {
            visited.insert(srcInstr);
            for (auto U : srcInstr->users()) {
                if (auto I = dyn_cast<Instruction>(U)) {
                    if (dyn_cast<StoreInst>(I) || dyn_cast<LoadInst>(I)) {
                        targetMemAccesses.insert(I);
                        currVal = true;
                    }
                    currVal = MemAccessFetcher::getTargetMemAccessRecursive(I, visited, targetMemAccesses) || currVal;
                }
            }
        }
        return currVal;

    }
    bool MemAccessFetcher::getTargetMemAccess(Instruction *srcInstr, std::set<Instruction*> &targetMemAccesses) {
        std::set<Instruction*> visitedInstrs;
        visitedInstrs.clear();
        return MemAccessFetcher::getTargetMemAccessRecursive(srcInstr, visitedInstrs, targetMemAccesses);
    }

    bool MemAccessFetcher::hasConstantOperand(Value *pointerOperand) {
        Value *stripPtrOp = pointerOperand->stripPointerCasts();
        return dyn_cast<Constant>(stripPtrOp) != nullptr && dyn_cast<GlobalVariable>(stripPtrOp) == nullptr;
    }
}