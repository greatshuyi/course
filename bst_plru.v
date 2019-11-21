
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
// To used this module, caller must be explicitly instantiate registers to hold
// LRU history vectors and **its initial value An Instantiation example as follow:
//
//     ...
//     parameter NWAY = 4;
//     parameter LRU_WIDTH = NWAY - 1;
//
//     ...
//
//     // LRU history vector registering
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
//  the access history(age history) info. The heart of the algorithm is to representation
//  access hitory(LRU history) using a bst, in which, each node except leafs is a 
//  one-bit flag denoting which child node (left or right) is more least recently
//  used, and each leaf node is just a pointer to a item. Upon each access, this 
//  algorithm starts a traverse from the root guided by internal nodes' direction
//  until a leaf node been reached.
//  
//  Let the binary operator > represents the relative age between left and right children,
//  i.e. x > y means x is less recently accessed than that of y. Hence, tree taverseing 
//  should follow the left child. 
//
//  Taking 4-item as an examaple, we label these four entries from 0 to 3, and
//  compose a BST tree as follow:
//                     
//                     
//                      root
//                       |
//                       |
//                   lru[0]==0             
//                  /         \             
//                 y           n            
//                /             \           
//          lru[2]==0         lru[1]==0      
//            /   \             /   \       
//           y     n           y     n
//          /       \         /       \     
//      item[3]   item[2]  item[1]   item[0]
//
//   
//
// state | replace              ref to | next state
// ------+--------              -------+-----------
//  00x  | item[0]               item0 |    11_
//  01x  | item[1]               item1 |    10_
//  1x0  | item[2]               item2 |    0_1
//  1x1  | item[3]               item3 |    0_0
//
// ('x' means don't care)       ('_' means unchanged)
      
//               relative age information between each pair of element upon every access.
//  An intuitive way is to use comparators to accomplish it. However, a
//  neat approach exists not only to store the coded history efficiently,
//  but also easing the aging info's calculation.
// 
//  To elaborate this method, we start from studying how to express the 
//  whole information of whether certain entry is older than others.
//  
//
//  Using above notation, and in case of four-way entries example,
//  the total relative age information can be expressed as follow:
//
//      |3>2|3>1|3>0|2>3|2>1|2>0|1>3|1>2|1>0|0>3|0>2|0>1|
//
//  The above information can be re-arranged in a more elegant and concise
//  way by utilizing a binary-valued matrix(Age matrix):
//
//                >    3      2      1      0
//                3    *    (3>2)  (3>1)  (3>0)
//                2  (2>3)    *    (2>1)  (2>0)
//                1  (1>3)  (1>2)    *    (1>0)
//                0  (0>3)  (0>2)  (0>1)    *               
// 
//  The value of element(i, j) tells the relative age on two enties: 1 if and
//  only if entry i older than entry j. The diagonal elements are special cases,
//  since each entry cannot compare age information with itself. So a "*" is
//  given meaning that the final outcome is irrelevant with these elements.
//
//  Take a closer look at the age matrix, and it's clear that it is redundant
//  becuase two entries can never be equally old. In a mathmatical way, for any
//  two given entries, we have the following equation holds:
//                         x>y == !y>x,
//  By applying above equation to age matrix and set the diagonal element
//  to constant '1', it leads to a simpler symmetric representation:
//
//                >     3      2       1       0
//                3     *    (3>2)   (3>1)   (3>0)
//                2  !(3>2)    *     (2>1)   (2>0)
//                1  !(3>1)  !(2>1)    *     (1>0)
//                0  !(3>0)  !(2>0)  !(1>0)    *   
//
//                            ||
//                            ∨ 
//
//              MSB   | 5 | 4 | 3 | 2 | 1 | 0 |   LSB
//                    |3>2|3>1|3>0|2>1|2>0|1>0|
//
//  As can be seen from this simpler matrix, the lower half is just the
//  inverted mirror of the upper half. As a result, the width of LRU vector
//  is the number of upper matrix elements and their values tell relative age
//  in a compact way. Further, by using either the upper half or lower half
//  of the age matrix, the 4-way LRU bit-vector represents age information as
//  follow(suppose in row-major order):
//

//
//  The calculations on this vector are much simpler and it is therefore used 
//  by this module. 
//  The bit-width used to hold LRU history is determined by:
//
//                    WIDTH = NWAY*(NWAY-1)/2.
//
//  Based on this neat method, the LRU calculation algorithm using
//  upper half matrix representation performs as:
//
//    1. Form a age matrix with incoming LRU vector(current LRU vector),
//       specifically the diagonal element (i,i) is set to statically one,
//       which, in turn can be omitted.
//
//    2. The LRU_pre vector is the vector of the ANDs of the each row.
//
//    3. Generate next LRU values with the access vector (if any) in
//       following way: If access[i] is set, the values in row i are
//       set to 0. Similarly, the values in column i are set to 1.
//
//    4. The update vector of the lru history is then generated by
//       copying the upper half of the matrix back.
//
//    5. The LRU_post vector is the vector of the ANDs of each row.
//
//  Take following example as a demonstration:
//
//    NWAY    = 4
//    current = 6'b110100;
//    access  = 4'b0001;
//
//  Assuming LRU vector represents relative age as follow:
//
//        | 3>2 | 3>1 | 3>0 | 2>1 | 2>0 | 1>0 |
//           1     1     0     1     0     0
//           
//    a. age matrix can be formed as:
//        > | 3 2 1 0
//        -----------
//        3 | 1 1 1 0
//        2 | 0 1 1 0  => 0 > 3 > 2 > 1
//        1 | 0 0 1 0
//        0 | 1 1 1 1
//    
//       which means 0-th is the least recently used item
// 
//    b. lru_pre can be calculated: 
//        
//        lru_pre[3] = 0
//        lru_pre[2] = 0
//        lru_pre[1] = 0
//        lru_pre[0] = 1 => means it's the least recently used(oldest)
//
//    c. now, update age matrix with access vector 4'b0001, the matrix become
//
//        > | 3 2 1 0
//        -----------
//        3 | 1 1 1 1
//        2 | 0 1 1 1  => 3 > 2 > 1 > 0
//        1 | 0 0 1 1
//        0 | 0 0 0 1
//
//     d. updated LRU vector copied from upper half of the updated matrix
//
//        | 3>2 | 3>1 | 3>0 | 2>1 | 2>0 | 1>0 |
//           1     1     1     1     1     1
//
//     e. post_lru , or more precisely, the least recently used vector is 
//        ANDs of each row
//
//        lru_pre[3] = 1 => means it's now the least recently used one(oldest)
//        lru_pre[2] = 0
//        lru_pre[1] = 0
//        lru_pre[0] = 0 
//
//
//



module bst_lru #(

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
wire [DEPTH-1:0] pre_bst_matrix [NWAY-1:0];
wire [DEPTH-1:0] post_bst_matrix [NWAY-1:0];

genvar r, c;


///////////////////////////////////////////////////////
// LRU algorithm
///////////////////////////////////////////////////////

// 1. Form mirrored bst matrix

generate
for (r = 0; r < DEPTH; r = r + 1) begin: pre_bst_row
	for (c = 0; c < NWAY; c = c + 1) begin: pre_bst_col
		
		if ( ((c >> (depth-1-r)) % 2) == 0 ) begin: right
			assign pre_bst_matrix[c][r] =  current[LRUW - (2**r) - (c >> (DEPTH - r))];
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


//  3. Update matrix, make sure the access vector is one-hot encoded.
//     If access[i] is set, the values in row i are set to 0. Similarly, 
//     the values in column i are set to 1(Vice Verser).

generate
for (r = 0; r < NWAY; r = r + 1) begin: post_matrix_row
	for (c = 0; c < NWAY; c = c + 1) begin: post_matrix_col
	
		if (r==c) begin: diagonal
			assign post_matrix[r][c] = pre_matrix[r][c];
		end else begin: non_diagonal:
			assign post_matrix[r][c] = (access[c] | ~access[r] & pre_matrix[r][c]);
		end
	
	end
end
endgenerate


// 4. The updated vector of the lru history is then generated by
//    copying the inversion of lower half of the post matrix back.

generate
for (r = 1; r < NWAY; r = r + 1) begin: post_lru_row
	for (c = 0; c < r; c = c + 1) begin: post_lru_col
	
		assign update[2**(r-1)+c] = post_matrix[r][c]
end
endgenerate


// 5. The LRU_post vector is the vector of the ANDs of each row
//    on post matrix.

generate
for (r = 0; r < NWAY; r = r + 1) begin: post_lru

    lru_post[r] = &post_matrix[r];

end
endgenerate



endmodule
