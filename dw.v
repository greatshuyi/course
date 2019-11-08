

`include "lib.vh"


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


module encode #(

	parameter IW = 8,
	parameter OW = `CLOG2(IW)

) (

	input  [IW-1:0] in,
	output [OW-1:0] out,
	output          vld			// asserts in contains at least one '1' bit

);

integer i;
reg [OW-1:0] tmp;
always @(*) begin
	tmp = 0;
	for (i=0; i<IW; i=i+1) begin
		if (in[i])
			tmp = i;
	end
end

assign vld = &(~in);
assign out = tmp;

endmodule

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


module decode #(

	parameter IW = 3,
	parameter OW = 2**IW
) (
	input            en,
	input  [IW-1:0]  in,
	output [OW-1:0]  out
	output           vld
);

genvar i;

generate
	for(i=0;  i< ; i=i+1) begin: dec
		assign out[i] = (in == i); 
	end
endgenerate

assign vld = en; 

endmodule


module group_match #(
	parameter IN_WIDTH = 16,
	parameter OUT_WIDTH = 4,
) (
	input wire [IN_WIDTH-1:0] in,
	output wire [OUT_WIDTH-1:0] out
);
	
	reg [OUT_WIDTH-1:0] valid;
	integer i;
	always @(*) begin
		valid[i] = |(in[(IN_WIDTH-i*OUT_WIDTH)-1: OUT_WIDTH]);
	end
	
	assign out = valid;
	
endmodule

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



module rotate #(

	parameter DW = 16,
	parameter NG = 8,
	parameter DIRECTION = "LEFT"
	
) (
    input           ren,
	input  [NG-1:0] rotate,
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

encode #(.IW(NG) ) sel_enc (
	.in(rotate),
	.out(idx),
	.vld(idx_vld)
);

assign dout = shift[idx];

endmodule
