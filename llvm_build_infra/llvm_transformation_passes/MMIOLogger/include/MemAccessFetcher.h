//
// Created by machiry on 2/27/19.
//

#ifndef PROJECT_MEMACCESSFETCHER_H
#define PROJECT_MEMACCESSFETCHER_H
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
    /***
     * The class that handles getting referenced memory access instrution.
     */
    class MemAccessFetcher {
    private:
        /***
         * Similar to getTargetMemAccess but a recursive version.
         * @param srcInstr Same as the original function.
         * @param visited Set of already visited instructions.
         * @param targetMemAccesses target memory instruction.
         * @return True (f at least one instruction is added) else false.
         */
        static bool getTargetMemAccessRecursive(Instruction *srcInstr,
                                                std::set<Instruction*> &visited,
                                                std::set<Instruction*> &targetMemAccesses);
    public:
        /***
         * Get target memory instructions derived from the given instruction.
         *  Example:
         *  %PIO_LSR25 = getelementptr inbounds %struct.Pio, %struct.Pio* %33, i32 0, i32 44, !dbg !341
         *   store volatile i32 %32, i32* %PIO_LSR25, align 4, !dbg !342
         *
         *   Given instruction, %PIO_LSR25 = getelementptr inbou ..
         *   This will return the store instruction.
         *
         * @param srcInstr The source instruction whose derived memory access should be fetched.
         * @param targetMemAccesses Result memory access instructions.
         * @return True (f at least one instruction is added) else false.
         */
        static bool getTargetMemAccess(Instruction *srcInstr,
                                       std::set<Instruction*> &targetMemAccesses);
    };
}
#endif //PROJECT_MEMACCESSFETCHER_H
