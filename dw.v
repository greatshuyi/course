
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
	output [OW-1:0] out
	output          vld

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


module pop_cnt();


endmodule
