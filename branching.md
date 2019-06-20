

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
  

## 动态分支预测

### 相关预测（两级预测）

考虑这样的问题，如果在分支预测时，不仅只考虑当前分支的行为，还能够考虑其他分支的行为，就有可能提高准确率。相关预测就是此类预测器，也称为
两级预测。相关预测器通过考查指令流中最近已执行过分支的结果（全局信息），来预测当前分支。该类分支预测一般被记为(m, n)预测器。一个(m, n)预测器
利用最近m个分支的行为从2^m个分支预测器中进行选择，其中每个预测器都为一个单分支的n位预测器。例如，一个(1, 2)相关预测器在预测一个特定分支时，
利用最近一个分支的行为从(2^1)两个2位分支预测器中进行选择。

从实现上来看，正如相关预测的另一个称谓两级预测所表明的那样可被划分成两级。最近m个分支的全局历史，显然可以用一个m位的以为寄存器实现，这一级也常被
称谓BHR(Branch History Register，也称为BHT，Branch History Table)；第二级为一个至少是2^m项的表，每个项为一个n比特的饱和计数器，这一级也被称
为PHT(Pattern History Table). 第一级在当前分支被执行确认后，其结果移入BHR中，相对应第二级通过BHR值经处理后(见后续)索引到对应项后，根据跳转执
行结果完成状态跳转。

#### 全局预测器（global branch predictor）

相关预测的一个主要问题就是如何实现的问题。我们知道，再确定BHR的值后可以通过该值所引导PHT对应的表项，但其中缺少一个关键环节：当前分支如何被引入到决策
过程中？全局预测器就用以解决该问题。首先，将当前指令的低位地址串接到BHR值的后面，然后以该串接值作为PHT表的索引项。从实现上来看，这一结构有多种变体。
假设以指令最后4位地址串接到BHR，则PHT表项共有2^m * 2^n项；当然在设计时该过程完全可以反过来，假设受到面积约束，PHT表项只能取64项，那么完全可以只
取指令的最后6位，或者更近一步，任取大于6位，然后经压缩译码变换为6位。总之，可以灵活选取配置。以Pentium为例，BHR使用了一个4bit的移位寄存器做为BHR，
PHT则分为多个实体物理实体表，表之间采用指令低地址进行索引。

##### gshare predictor

全局预测器的一个重要变体即为gshare预测器，其基本框架即为全局预测器。不同的是，其BHR宽度与所选的指令低地址宽度相同，在预测时先将BHR与地址异或，然后用
该值来索引PHT，该结构有如下特点：

 + 引入了更多的上下文信息
 + 提升了PHT的利用率
 + 增大的PHT的访问延迟
 
#### 局部预测器（Local branch predictor）

相关预测器的思想也可以应用到如下改进思想上：将同一分支的前一次执行的预测结果与当前执行进行相关。这就是局部预测器。这一结构下仍然可以用前述的两级预测器
结构来概括，其核心不同点是在BHR的构建，以及如何索引PHT的方法上。在局部预测器上实现中，BHR为实现为一个阵列，每个阵列为一个mbit的以为寄存器（即为全局
预测器中的BHR），该阵列则使用指令的低地址进行索引；PHT的索引则以BHR对应表项的值来索引。

总结：二维BHR，然后用BHR entry索引PHT

#### 竞赛预测器（tournament predictor）



#### 双峰预测器（Bimodal predictor）


#### TAGE predictor


一些已有结论：

1. 简单的BP方案查询时间短，能效高但预测精度低；
2. 复杂的BP方案，无论是neural-based 或者 variants of two level branch predictor准确度高，但复杂、功耗高，而且致命的一点是预测消耗的cycle数高，可能
会在2~5cycle间波动；
3. BP的终极目标明确，提升准确率，降功耗，降实现复杂度


