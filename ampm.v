/*
1. The memory address space is divided into regions of fixed size, in which each region is called a ZONE;
2. The Number of cache lines in one zone is equal to the number of the entries in the bitmap-like data structure;
3. 
*/

module cam_entry #(
	
	parameter WIDTH = 16

) (
	input clk,
	input rst_n,
	
	input alloc,
	input dealloc,
	
	input [WIDTH-1:0] din,
	output            valid,
	output [WIDTH-1:0] cam
);
	
	
// valid bit
always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		valid <= 1'b0;
	else begin
		case({alloc, dealloc})
			2'b10, 2'b11:	valid <= 1'b1;
			2'b01       :	valid <= 1'b0;
			default     :	valid <= valid;
		endcase
	end
end

// payload
always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		valid <= 1'b0;
	else begin
		if (alloc)
			cam <= din;
		else
			cam <= dam
	end
end

endmodule
	


module cam #(

	parameter CAMW = 16,
	parameter NCAM = 16,
	parameter NWAY = 3
	
) (
	input                  clk,
	input                  rst_n,
	
	input wire             cam_vld [NWAY-1:0],
	input wire [CAMW-1:0]  cam_din [NWAY-1:0],
	input wire [NCAM-1:0]  cam_hit [NWAY-1:0],
	                       
	input wire             wen,
	input wire [NCAM-1:0]  widx,
	input wire [CAMW-1:0]  wdata,
	
	input wire [NCAM-1:0]  dealloc,
	
);


wire [NCAM-1:0] entry_alloc = widx & {NCAM{wen}};
wire [CAMW-1:0] entry_wdata = wdata;

wire [NCAM-1:0] entry_valid;
wire [CAMW-1:0] entry_cam [NCAM-1:0];

wire [NCAM-1:0] entry_dealloc = dealloc;

genvar i, w;

///////////////////////////////////////////////////////
// CAM array
///////////////////////////////////////////////////////

generate
for(i=0; i<NCAM; i++) begin: cam_array
	cam_entry #(.WIDTH(CAMW)) 
	entry (
		.clk(clk),
		.rst_n(rst_n),
		.alloc(entry_alloc[i]),
		.dealloc(entry_dealloc[i]),
		.din(entry_wdata),
		.valid(entry_valid[i]),
		.cam(entry_cam[i])
	);
end
endgenerate


///////////////////////////////////////////////////////
// CAM search
///////////////////////////////////////////////////////

// hit on cam entry
wire [NCAM-1:0] array_hit [NWAY-1:0];
wire [NWAY-1:0] alloc_hit;

generate
for(w=0; w<NWAY; w=w+1) begin: way_search
	for(i=0; i<NCAM; i++) begin: array_search
		assign array_hit[w][i] = (entry_valid[i] & ~entry_deallloc[i]) & 
		                         (entry_cam[i] == cam_din);
	end
end	
endgenerate

// hit on alloc data
generate
for(i=0; i<NWAY; i++) begin: alloc_search
	assign alloc_hit[w] = (cam_vld[w] & cam_alloc[w]) & (cam_din == entry_wdata);
end
endgenerate

// final hit vector
generate
for(i=0; i<NWAY; i++) begin: alloc_search
	assign cam_hit[w] = alloc_hit[w] ? entry_alloc  : 
	                    cam_vld[w]   ? array_hit[w] : {NCAM{1'b0}};
end
endgenerate


///////////////////////////////////////////////////////
// Hit vector encoding
///////////////////////////////////////////////////////

wire [CAM_HIT_W-1:0] cam_mhit [NCAM-1:0];

generate
encode #(
) hit_enc (
	.in({})
	.out(

endgenerate
///////////////////////////////////////////////////////
// LRU ctrl
///////////////////////////////////////////////////////

// if there is non-valid entry, use it first

wire empty_entry = ~(&entry_valid);
assign entry_lru = empty_entry ? alloc_lru ? 


endmodule

`define P_INIT = 0;
`define P_ACCE = 1;
`define P_PRFT = 2;
`define P_SUCC = 3;



module pattern_entry #(
	parameter NSTATE = 2,
	parameter NLINE  = 8
) (
	input        clk,
	input        rst_n,
	
	input                          vld,
	input                          clr,
	input  wire [NLINE-1:0]        req,
	
	output wire [NSTATE*NLINE-1:0] data
	
);

localparam WIDTH = NSTATE * NLINE;

localparam [NSTATE-1:0] P_INIT = 0;
localparam [NSTATE-1:0] P_PRFT = 1;
localparam [NSTATE-1:0] P_ACCE = 2;
localparam [NSTATE-1:0] P_SUCC = 3;

reg [WIDTH-1:0] state

genvar i;

generate
for (i=0; i<NLINE; i=i+1) begin: state_entry
	always @(posedge clk) begin
		if (clr & vld)
			state[i*NSTATE :+ NSTATE] <= P_INIT;
		else begin
			case(state[i*NSTATE :+ NSTATE])
				P_INIT: begin
					if (req & vld)	// demand access
						state[i*NSTATE :+ NSTATE] <= P_ACCE;
					else if (~req & vld)
						state[i*NSTATE :+ NSTATE] <= P_PRFT;
					else
						state[i*NSTATE :+ NSTATE] <= state[i*NSTATE :+ NSTATE];
				end
				
				P_PRFT: begin
					if (req & vld)
						state[i*NSTATE :+ NSTATE] <= P_SUCC;
					else
						state[i*NSTATE :+ NSTATE] <= state[i*NSTATE :+ NSTATE];
				end
				
				P_ACCE, P_SUCC:
					state[i*NSTATE :+ NSTATE] <= state[i*NSTATE :+ NSTATE];
			endcase
		end
	end
end
endgenerate

assign data = state;

endmodule



module pattern_table (

	// actually a two port sram with write first
	
	
);

reg [STATEW-1:0] entry_data

///////////////////////////////////////////////////////
// Table entry
///////////////////////////////////////////////////////

pattern_entry #(
	
	.NLINE(8),
	.NSTATE(2)

) entry (
	.clk(clk),
	.rst_n(rst_n),
	
	.vld(entry_sel_vld),
	.clr(entry_clr),
	.req(entry_req),
	
	.data(entry_data)
)


endmodule


module patter_match_cell #(
	parameter SYMBOLW = 2,
	parameter PATTERN = 
) (
	input [PATTERNW-1:0]
	output               match
);

/*******************************
 * in apple's patents, the state of a cacheline defined as follow:
 * A: demand accessed
 * P: prefetched(actually prefetch request generated)
 * L: prefetched to lower cache(actually prefetched request generated)
 * S: successful prefetched
 * .: invalid
 * status extended by APPLE:
 * PP: prefetch in progress
 * LP: prefetch to lower cache in progress

	
	
endmodule




module pattern_matching #(

) (
	input 
);





endmodule


