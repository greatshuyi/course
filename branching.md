

BP在当前体系结构中的重要性

+ 分支指令整体占比高（经验值>=20%)，另一方面Average run-length between branch
+ 分支代价：
  + 多级流水：多级流水意味着从取指后需要更多的cycle才能知道分支结果，因此stall周期长，如果不stall那么分支后的惩罚太高；
  + 多反射/多线程：此类架构意味着几乎每个cycle都会有分支发生，如果不处理意味着大量的flush/re-fetching操作；
  + 面向对象： 将导致更多的间接分支的产生；
  + 占比问题：如果其他问题导致的stall降下来了，那么分支导致的CPI占比部分就凸显出来了；
  
  
BP在CA中演进方向：
 + 提升预测准确率：
  + 2-level correlating(adaptive) predictor: Core i7, Cortex-A8, Pentiums
  + use both history & branch address: Cortex-A8, MIPS
  + tournament predictor: Pentium 4, Power5
 + 尽早确定返回地址:
  + branch target buffer: all chips
  + next address in ICache: UltraSPARC
  + return address stack: all chips
  
  






从指令流及最终的分支结果角度来看，实际上就划分为如下几类：

direct conditional branch
direct unconditional branch
indirect conditional branch
indirect unconditional branch

1. forward conditional branch: 运行期结果决定，最终PC值在指令流中前移；
2. backward conditional branch：最终PC值在指令流中后移，例如continue到loop起始处；
3. unconditional branch：包括jump，procudure call， return


BP方案

静态分支：在整个程序执行期间都执行相同的分支预测策略，比如总是取执行或不执行中的一种结果。

实现方式：

 + 软件实现：
 在分支语句中用1bit告知compiler当前分支预测的方向
 
 + 硬件实现：
  + 永远不执行分支(predict always not taken)
  + 永远执行分支(predict always taken)
  + 总执行前向，不执行后向(backward branch predict taken, forward branch predict not taken)
  

### 动态分支预测

#### 相关预测（两级预测）

考虑这样的问题，如果在分支预测时，不仅只考虑当前分支的行为，还能够考虑其他分支的行为，就有可能提高准确率。相关预测就是此类预测器，也称为
两级预测。相关预测器通过考查指令流中最近已执行过分支的结果，来预测当前分支。该类分支预测一般被记为(m, n)预测器。一个(m, n)预测器利用最近
m个分支的行为从2^m个分支预测器中进行选择，其中每个预测器都为一个单分支的n位预测器。例如，一个(1, 2)相关预测器在预测一个特定分支时，利用最近
一个分支的行为从(2^1)两个2位分支预测器中进行选择。


一些已有结论：

1. 简单的BP方案查询时间短，能效高但预测精度低；
2. 复杂的BP方案，无论是neural-based 或者 variants of two level branch predictor准确度高，但复杂、功耗高，而且致命的一点是预测消耗的cycle数高，可能
会在2~5cycle间波动；
3. BP的终极目标明确，提升准确率，降功耗，降实现复杂度


