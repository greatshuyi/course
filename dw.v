
`include "lib.vh"
//-------------------------------------------------------------------------
// Parameterized Multi-lane Single-bit Mux
//-------------------------------------------------------------------------
module mux #(
	parameter LANE = 4;
) (

	input   wire [LANE-1:0] in,
	input   wire [LANE-1:0] sel,
	input   wire            de,				// default output value if invalid selection applied
	output  wire            out
);	

genvar i;

wire [LANEM-1:0] vector;

generate
for (i = 0 ; i < LANE; i = i + 1) begin: OR_TREE

	assign vector[i] = sel[i] ? in[i] : 1'b0;

end
endgenerate

wire res = |vector;
assign out = (|sel) ?  : de

endmodule /* mux */



//-------------------------------------------------------------------------
// Parameterized Multi-bit multi-lane Mux
//-------------------------------------------------------------------------
module vmux #(

	parameter LANE = 4,
	parameter WIDTH = 16
	
) (
	input   wire [WIDTH-1:0] in [LANE-1:0] ,
	input   wire [LANE-1:0]  sel,
	input   wire [WIDTH-1:0] de,
	output  reg  [WIDTH-1:0] out
);

genvar l, w;

wire [LANE-1:0] mxn [WIDTH-1:0];

generate
	for (w = 0; w < WIDTH; w = w + 1) begin: row
		for (l = 0; l < LANE; l = l + 1) begin: col
			assign mxn[w][l] = in[l][w];
		end
	end
endgenerate

generate begin
	for (w = 0 ; w < WIDTH; w = w + 1) begin
		
		mux #(
			.LANE(LANE) ) 
		mx (
			.in(mxn[w]),
			.sel(sel),
			.de(de[w]),
			.out(out[w]))
	end
end

endmodule /* vmux */


//-------------------------------------------------------------------------
// Parameterized Multi-bit bus reverser
//-------------------------------------------------------------------------
module reverse #(
	parameter WIDTH = 16
) (
	input  wire [WIDTH-1:0] in,
	output reg  [WIDTH-1:0] out
);

integer i;
always @(*) begin
	for (i=0; i<WIDTH; i=i+1) begin
		out[i] = in[WIDTH-i-1];
	end
end

endmodule


//-------------------------------------------------------------------------
// Parameterized Binary Encoder
//-------------------------------------------------------------------------
module encode #(

	parameter IWIDTH = 8,
	parameter OWIDTH = `CLOG2(IWIDTH)

) (

	input  [IWIDTH-1:0] in,
	output [OWIDTH-1:0] out,
	output              vld			// asserts in contains at least one '1' bit

);

integer i;
reg [OWIDTH-1:0] tmp;
always @(*) begin
	tmp = 0;
	for (i=0; i<IWIDTH; i=i+1) begin
		if (in[i])
			tmp = i;
	end
end

assign vld = &(~in);
assign out = tmp;

endmodule /* encode */



//-------------------------------------------------------------------------
// Parameterized Binary Decoder
//-------------------------------------------------------------------------
module decode #(

	parameter IWIDTH = 3,
	parameter OWIDTH = 2**IWIDTH
	
) (
	input                en,
	input  [IWIDTH-1:0]  in,
	output [OWIDTH-1:0]  out
	output               vld
);

genvar i;

generate
	for(i = 0; i < OWIDTH ; i = i + 1) begin: dec
		assign out[i] = en & (in == i); 
	end
endgenerate

assign vld = en; 

endmodule /* decode */



//-------------------------------------------------------------------------
// LSB-first, Parameterized First zero detector
//-------------------------------------------------------------------------
module leading_zero_detector #(
	parameter WIDTH = 8,
) (
	input  wire [WIDTH-1:0] in,
	output wire [WIDTH-1:0] out,
	output                  vld
);

// LSB-first leading zero detector

genvar i;

generate
for (i=0; i<WIDTH; i=i+1) begin: lzd
	if (i==0) begin: THRU
		assign out[i] = ~in[i];
	end else if begin: SINGLE:
		assign out[i] = ~in[i] & in[i-1];
	end else if begin: MULTI
		assign out[i] = ~in[i] & (&in[i-1:0]);
	end
end:lzd
endgenerate

assign vld = ~(&vld);

endmodule



//-------------------------------------------------------------------------
// Parameterized One-hot Checer
//-------------------------------------------------------------------------
module check_onehot #(

    parameter WIDTH = 4

) (

    input  wire [WIDTH-1:0] in,
    output wire             out

);

localparam integer ONE = 1;

reg ohot;
integer i;

always @(*) begin
    for(i=0; i<WIDTH; i=i+1) begin
        ohot[i] = (in == (ONE << i)) ? 1'b1 : 1'b0;
    end
end

assign out = | ohot;

endmodule




//-------------------------------------------------------------------------
// Parameterized one-hot to thermal convertor
//-------------------------------------------------------------------------
module onehot2thermal #(
    parameter WIDTH = 32,
    parameter DIRECTION = "LSB"         // priority direction
) (
    input  wire [WIDTH-1:0] in,
    output wire [WIDTH-1:0] out
);


//    Functinonal Truth Table
//    DIRECTION == LSB
//    in         out
//    0 0 0 0    0 0 0 0
//    0 0 0 1    0 0 0 1
//    0 0 1 x    0 0 1 1
//    0 1 x x    0 1 1 1
//    1 x x x    1 1 1 1
//    DIRECTION == MSB
//    in         out
//    0 0 0 0    0 0 0 0
//    1 0 0 0    1 0 0 0
//    X 1 0 0    1 1 0 0
//    X X 1 0    1 1 1 0
//    X X X 1    1 1 1 1


genvar i;

generate if (DIRECTION == "LSB") begin: LSB
    for (i=0; i<WIDTH; i=i+1) begin
	
        assign out[i] = |in[WIDTH-1: i];
    
	end
end else begin: MSB
    for (i=WIDTH-1; i>=0; i=i-1) begin
        
		assign out[i]= |in[i: 0];
    
	end
end
endgenerate

endmodule



//-------------------------------------------------------------------------
// Parameterized variable-width rotator
//-------------------------------------------------------------------------
module rotate #(

	parameter DW = 16,
	parameter NG = 8,
	parameter DIRECTION = "LEFT"
	
) (
    input              ren,
	input  [NG-1:0]    rotate,
	input  [DW*DW-1:0] din,
	output [DW*NG-1:0] dout,
	
);

localparam STRIDE = DW / NG;
localparam NGW = `CLOG2(NG);


reg [DW*NG-1:0] shift [NG-1:0];

wire [NGW-1:0] idx;
wire           idx_vld;

generate begin
	if (DIRECTION == "LEFT") begin: LSH
	
		always @(*) begin
			shift[0] = din;
			for (i=1; i<NG; i=i+1) begin
				shift[i] = {shift[i-1][DW*(NG-1)-1:0], shift[i-1][DW*NG-1: DW*(NG-1)]};
			end
		end
		
	end else begin: RSH
	
		always @(*) begin
			shift[0] = din;
			for (i=1; i<NG; i=i+1) begin
				shift[i] = {shift[i][DW-1:0], shift[i-1][DW*NG-1:DW]};
			end
		end
	
	end
endgenerate

encode #(.IWIDTH(NG) ) 
sel_enc (
	.in(rotate),
	.out(idx),
	.vld(idx_vld) );

assign dout = shift[idx];

endmodule

//-------------------------------------------------------------------------
// Parameterized multi-lane comparator matrix
//-------------------------------------------------------------------------

module age_matrix #(
	parameter NLANE = 4,
	parameter   = 6,
	
) (
	input [AGEW-1:0]   ival [NLANE-1:0],
	input [NLANE-1:0]  ivld
);
endmodule
	
