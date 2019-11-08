module mctx_ll_queue_entry #(
	
	parameter DW = 16,
	parameter PTRW = 5
	
) (
	input wire             clk,
	input wire             rst_n,
	input wire             allocate,
	input wire             deallocate,
	input wire [DW-1:0]    din,

	input                  link,
	input                  ptr

	output reg             valid,
	output reg [DW-1:0]    dout,
	output reg [PTRW-1:0]  nptr
);

///////////////////////////////////////////////////////
// paramter & arch register
///////////////////////////////////////////////////////

// valid
always @(posedge clk or negedge rst_n)
	if (!rst_n)
		valid <= 0;
	else begin
		case({deallocate[i], allocate[i]})
			2'b1?:
				valid <= 1'b0;
			2'b01:
				valid <= 1'b1;
			default:
				valid <= valid;
		endcase
	end
end

// payload
always @(posedge clk) begin
	if (allocate)
		dout <= din;
	else
		dout <= dout;
end

// link list ptr
always @(posedge clk) begin
	if (link & valid)
		nptr <= ptr;
	else
		nptr <= nptr;
end

endmodule


module mctx_ll_queue #(

	parameter NCTX = 16,
	parameter WIDTH = 16,
	parameter DEPTH = 
	
) (

	input wire clk,
	input wire rst_n,
	
	// write control
	input wire             put,
	input wire [NCTX-1:0]  pctx,
	input wire [WIDTH-1:0] din,
	output wire full,
	
	
	// read control
	input wire              get,
	input wire  [NCTX-1:0]   gctx,
	output wire [WIDTH-1:0] dout,
	output wire [NCTX-1:0]  empty;
	
);


///////////////////////////////////////////////////////
// paramter & arch register
///////////////////////////////////////////////////////
local GWCNTW = `CLOG(DEPTH);	// global entry counter
local PTRW = GWCNTW;			// w/r current/next pointer width
local ENTRYW = WIDTH + NPTRW;	// entry width


// global write counter
reg [GWCNTW-1:0] gwcnt;
reg [DEPTH-1:0]  valid;

wire safe_put = put & ~full & ~;
wire safe_get;

wire gwcnt_full = &gwcnt;
wire gwcnt_empty = ~(|gwcnt);

// put/get control
reg [PTRW-1:0] head [NCTX-1:0];
reg [PTRW-1:0] tail [NCTX-1:0];
wire [NCTX-1:0] empty;


///////////////////////////////////////////////////////
// write control
///////////////////////////////////////////////////////

// global write counter
always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		gwcnt <= 0;
	else begin
		case({safe_put, safe_get})
			2'b10:
				gwcnt <= gwcnt + 1;
			2'b01:
				gwcnt <= gwcnt - 1;
			default:
				gwcnt <= gwcnt;
		endcase
	end
end


genvar i;

// allocate/deallocate

wire [NCTX-1:0] next_valid;

priority_mask #(NCTX) alloc(
	.in(valid),
	.out(next_valid)
	);

wire [NCTX-1:0] allocate = {NCTX{safe_put}} & next_valid;

wire [PTRW-1:0] next_head;
wire [PTRW-1:0] next_tail [NCTX-1:0];

// next head always generates from first available entry's position
encoder #(
	.IWIDTH(NCTX),
	.OWIDTH(PTRW)
) ptr_dec (
	.in(next_valid),
	.out(next_head)
);



reg [ENTRYW-1:0] entries [DEPTH-1:0];


generate
for(i=0; i<NCTX; i=i+1) begin: head_pointer
	
	// head pointer
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			head[i] <= 0;
		else begin
			if (allocate[i])
				head[i] <= next_head;
			else
				head[i] <= head[i];
		end
	end
	
	// tail pointer
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			tail[i] <= 0;
		else begin
			if (empty[i] && allocate)
				tail[i] <= head[i] ;
			else if (deallocate[i])
				tail[i] <= next_tail[i];
			else
				tail[i] <= tail[i];
		end
	end
end
endgenerate



///////////////////////////////////////////////////////
// Entries
///////////////////////////////////////////////////////

wire [DEPTH-1:0] entry_allocate；
wire [DEPTH-1:0] entry_deallocate；
wire [DEPTH-1:0] entry_；


wire [WIDTH-1:0] entry_dout [DEPTH-1:0];
wire [DEPTH-1:0] entry_valid;

generate
for(i=0; i<DEPTH; i=i+1) begin: entries

	
	ll_queue_entry #(
		.WIDTH(WIDTH)
	) entry (
		.clk(clk),
		.rst_n(rst_n),
		.allocate(entry_allocate[i]),
		.deallocate(entry_deallocate[i]),
		.din(din),
		.link(entry_link[i]),
		.ptr(entry_ptr)
		.valid(entry_valid[i]),
		.dout(entry_dout[i])
		.nptr(entry_nptr[i])
	);
end


	
	// data field
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			entries[i] <= 0;
		else begin
			if (allocate[i])
				entries[i] <= {din, next_head};
			else
				entries[i] <= entries[i];
			endcase
		end
	end
	
	// output concantenation
	assign entry_dout[i] = entries[tail];
	assign next_tail[i] = entry_dout[i][0 +: PTRW];
	
end
endgenerate

generate
for(i=0; i<NCTX; i=i+1) begin: queue_entry

	// valid field
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			valid[i] <= 0;
		else begin
			case({allocate[i], deallocate[i]})
				2'b10:
					valid[i] <= 1'b1;
				2'b01:
					valid[i] <= 1'b0;
				default:
					valid[i] <= valid[i]
			endcase
		end
	end
	
	// data field
	always @(posedge clk or negedge rst_n)
		if (!rst_n)
			entries[i] <= 0;
		else begin
			if (allocate[i])
				entries[i] <= {din, next_head};
			else
				entries[i] <= entries[i];
			endcase
		end
	end
	
	// output concantenation
	assign entry_dout[i] = entries[tail];
	assign next_tail[i] = entry_dout[i][0 +: PTRW];
	
end
endgenerate


///////////////////////////////////////////////////////
// Queue output
///////////////////////////////////////////////////////

wire [PTRW-1:0] out_idx;

encoder #(
	.IWIDTH(NCTX),
	.OWIDTH(PTRW)
) out_id_enc (
	.in(gctx),
	.out(out_idx)
);
assign dout = (get & (|gctx)) ? entry_out[out_idx];


// empty flag for each context
generate
for(i=0; i<NCTX; i=i+1) begin: ctx_empty_gen
	assign empty[i] = (head[i] == tail[i]);
end
endgenerate



endmodule
