
//
//
// This is a binary search tree type pseudo-least-recently-used (pLRU) 
// calculation module. It essentially has two types of input and output.
//
//  * The LRU history information needs to be evaluated to
//    calculate the next LRU value.
//  * The one-hot encoded current access and the ways' LRU
//    selection value.
//
// This module is pure combinational. All registering is done outside
// this module.
//
// The following parameter exists:
//
//  * NWAY: Number of ways (must be greater than 1)
//
// The following ports exist:
//
//  * current:  The current LRU history
//  * next:     The new LRU history after access
//
//  * access:   all zeros if no access or one-hot of the way that accesses
//  * lru_pre:  LRU before the access (one hot of ways)
//  * lru_post: LRU after the access (one hot of ways)
//
// To use this module, caller must be explicitly instantiate registers to hold
// LRU history vectors and **its initial value An Instantiation example as follow:
//
//     ...
//     parameter NWAY = 4;
//     parameter LRU_WIDTH = NWAY - 1;
//
//     ...
//
//     // LRU history vector register
//     reg [LRU_WIDTH-1:0] current_history;
//     reg [LRU_WIDTH-1:0] updated_history;
//
//     // Access vector & Pre/Post LRU selection vector
//     wire [NWAY-1:0] access;
//     wire [NWAY-1:0] lru_pre;
//     wire [NWAY-1:0] lru_post;
//     ...
//
//     bst_lru (
//         .NWAY(4)
//     ) u_bst_lru (
//         .current  (current_history),
//         .update   (updated_history),
//         .access   (access),
//         .lru_pre  (lru_pre),
//         .lru_post (lru_post)
//     );
//
//
// Algorithm description:
//
//  To solve least-recently-used problem, the so-called binary-search-tree based 
//  pseudo-least-recently-used algorithm uses a slightly different way to track 
//  the access history(age history) info. The heart of the algorithm is how to 
//  represent access hitory(LRU history) using a bst, in which, each node except 
//  leaves is a one-bit flag denoting which child node (left or right) is more 
//  least recently used, and each leaf node is just a pointer to a item. Upon each 
//  access, this algorithm starts a traverse from the root guided by internal 
//  nodes' direction until a leaf node been reached.
//  
//  Let the binary operator > represents the relative age between left and right children,
//  i.e. x > y means x is less recently accessed than that of y. Hence, tree taverseing 
//  should follow the left child. 
//
//  Taking 8-item as an examaple, we label these four entries from 7 to 0, and
//  compose a BST tree from an initial lru vector 7'b0100110 as follow:
//
//                 [6]                                   0    
//            /            \                       /            \
//         [5]              [4]                  1                0
//       /      \         /     \     =>      /      \         /     \ 
//     [3]      [2]     [1]     [0]          0        1       1       0
//    /   \    /   \   /   \   /   \       /   \    /   \   /   \   /   \
//   L7   L6  L5   L4 L3   L2 L1   L0     L7   L6  L5   L4 L3   L2 L1   L0
//      
//  Then the item been accessed represented by 8'b0000100 is applied. BST is updated
//  by flipping along the path from designated ITEM to ROOT , and the bst tree become
//
//   
//                         1    
//                   /            \
//                 1                1
//              /      \         /     \         => LRU vector = 7'1110100
//             0        1       0       0
//           /   \    /   \   /   \   /   \
//          L7   L6  L5   L4 L3   L2 L1   L0
//                                 ^
//                                 |- accessed
//
//  To acommplish pLRU, we use a matrix based algorithm:
//
//    1. Form an initial bst matrix from initial lru history vector. The matrix size
//       is LEVEL x NWAYS. Row 0 corresponds to leaf nodes' level, Row[LEVEL-1] is 
//       root. Each 
//     
//
//
// 
// from functools import reduce
// from random import randint
// 
// def binv(x):
//     return 0 if x == 1 else 1
// 
// def bxor(x, y):
//     return 1 if x != y else 0
// 
// def band(x, y):
//     return 1 if x == 1 and y == 1 else 0
// 
// def bor(x, y):
//     return 1 if x == 1 or y == 1 else 0
// 
// def reduce_and(*l):
//     return reduce(band, l, 1)
// 
// def reduce_or(*l):
//     return reduce(bor, l, 0)
// 
// def reduce_xor(*l):
//     return reduce(bxor, l)
// 
// l = [0, 1, 1, 0, 1]
// 
// print("Reduced xor")
// r = reduce_xor(*l)
// print(r)
// print("Reduced and")
// r = reduce_and(*l)
// print(r)
// print("Reduced or")
// r = reduce_or(*l)
// print(r)
// print("Invert")
// r = binv(1)
// print(r)
// r = binv(0)
// print(r)
// 
// 
// def gen_seq(l, mode=1):
//     res = []
//     if mode == 1:
//         return [i for i in range(l)]
//     else:
//         for _ in range(l):
//             s = randint(0, l)
//             res.append(s % 2)
// 
//     return res
// 
// 
// nways = 16
// 
// depth = nways.bit_length() - 1
// width = nways
// 
// lruw = nways - 1
// 
// bst_matrix = [["" for _ in range(width)] for _ in range(depth)]
// vector = gen_seq(lruw)
// 
// 
// for r in range(depth):
//     for c in range(width):
//         i = lruw - (2**r) - (c >> (depth-r))
// 
//         if ( (c >> (depth-1-r)) % 2 ) == 0:
//             bst_matrix[r][c] = "{}".format(vector[i])
//             # bst_matrix[r][c] = vector[i]
//         else:
//             bst_matrix[r][c] = "-{}".format(vector[i])
//             # bst_matrix[r][c] = binv(vector[i])
// 
// print("bst_plru vector")
// print(vector)
// print("")
// print("pre_bst_matrix")
// for v in bst_matrix:
//     print(v)
// 
// access = gen_seq(nways)
// mask_matrix = [[4 for _ in range(lruw)] for _ in range(nways)]
// 
// 
// for b in range(depth):
//     for r in range(nways):
//         w = 2**(depth-1-b)
//         # print(w)
//         for c in range(w):
//             offset = nways - 2 ** (depth-b)
//             # print(offset)
//             if ( r >> (b+1) ) == c:
//                 mask_matrix[r][c+offset] = 1
//             else:
//                 mask_matrix[r][c+offset] = 0
// 
// 
// print("")
// print("")
// print("access vector")
// print(access)
// print("")
// print("mask_matrix")
// for v in mask_matrix:
//     print(v)


`include dw.v


module bst_plru #(

    parameter NWAY = 4,
	parameter LRUW = NWAY - 1;

) (

    input  wire [LRUW-1:0] current;
    output wire [LRUW-1:0] update;

    input  wire [NWAY-1:0] access;
    output wire [NWAY-1:0] lru_pre;
    output wire [NWAY-1:0] lru_post;

);

///////////////////////////////////////////////////////
// Parameter and Signals
///////////////////////////////////////////////////////

// LRU BST depth
localparam DEPTH = `CLOG2(NWAY);

// mirror BST matrix (original NWAY * DEPTH)
wire [DEPTH-1:0] pre_bst_matrix   [NWAY-1:0];
wire [DEPTH-1:0] post_bst_matrix  [NWAY-1:0];
wire [LRUW-1:0]  mask_matrix      [NWAY-1:0];


genvar r, c, b;


///////////////////////////////////////////////////////
// LRU algorithm
///////////////////////////////////////////////////////

// 1. Form an initial bst matrix

generate
for (r = 0; r < DEPTH; r = r + 1) begin: pre_bst_row
	for (c = 0; c < NWAY; c = c + 1) begin: pre_bst_col
		
		if ( ((c >> (depth-1-r)) % 2) == 0 ) begin: right
			assign pre_bst_matrix[c][r] = current[LRUW - (2**r) - (c >> (DEPTH - r))];
		else begin: left
			assign pre_bst_matrix[c][r] = ~current[LRUW - (2**r) - (c >> (DEPTH - r))];
		end
	
	end
end
endgenerate

	
//  2. The LRU_pre vector is produced from ANDs of the each row.

generate
for (r = 0; r < NWAY; r = r + 1) begin: pre_lru

    lru_pre[r] = &(pre_bst_matrix[r]);

end
endgenerate


//  3. Generate definitive initial mask matrix. This matrix is definitive 
//     and irrelevant with access/lru vector. The mask matrix is generated
//     block by block

generate
for (b = 0; b < DEPTH; b = b + 1) begin: mask_block
	for (r = 0; c < NWAY ; r = r + 1) begin: mask_row
		for (c = 0; c < (2**(DEPTH-b-1)); c = c + 1) begin: mask_col
		
			if ( (r>>(b+1) == c ) begin: lru_mask
				assign mask_matrix[r][c+nways - 2**(depth-b)] = 1'b1;
			end else begin: non_mask
				assign mask_matrix[r][c+nways - 2**(depth-b)] = 1'b0;
			end
		
		end
	end
end
endgenerate


// 4. The updated vector of the lru history is then generated by
//    copying the inversion of lower half of the post matrix back.


// 4.a.select mask vector according to access vector & mask matrix
wire [LRUW-1:0] mask;

vmux #(
	.LANE(NWAY),
	.WIDTH(LRUW) ) 
mask_mux(
	.in(mask_matrix),
	.sel(access),
	.de({LRUW{1'b0}}),
	.out(mask));


// 4.b.get updated LRU history vector( if no valid access
//     send out previous current directly)
assign update = ~(|access) ? current : current ^ mask;


// 5. Form post bst matrix from updated LRU vector

generate
for (r = 0; r < DEPTH; r = r + 1) begin: post_bst_row
	for (c = 0; c < NWAY; c = c + 1) begin: pre_bst_col
		
		if ( ((c >> (depth-1-r)) % 2) == 0 ) begin: right
			assign post_bst_matrix[c][r] = update[LRUW - (2**r) - (c >> (DEPTH - r))];
		else begin: left
			assign post_bst_matrix[c][r] = ~update[LRUW - (2**r) - (c >> (DEPTH - r))];
		end
	
	end
end
endgenerate




// 5. The LRU_post vector is the vector of the ANDs of each row
//    on post matrix.

generate
for (r = 0; r < NWAY; r = r + 1) begin: post_lru

    lru_post[r] = &post_bst_matrix[r];

end
endgenerate



endmodule


`ifdef BST_PLRU_SIM

module tb_bst_plru();



endmodule


`endif
