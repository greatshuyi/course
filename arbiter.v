`include "lib.vh"

// ### Fixed priority arbiter
//
// For fixed prioity aribter with N requests, the grant signals is generated by 
// finding the first asserted requestors starting from the highest priority(e.g. 
// MSB downto LSB or vice versa). For instance, the i-th grant signals out of N 
// requests with LSB priority is formed as follow:
//    gnt[i] = req[i] & (~(|req[i-1:0]));	// gnt[i] = req[i] & (&(~req[i-1:0]));
//
// ### Round robin arbiter
//


module fixed_priority_arbiter #(
	
	parameter NREQ = 4,
	parameter NIDX = `CLOG2(NREQ)
	
) (
	input               clk,
	input               rst_n,
	input               enable,
	input				repleinish,
	
	
	input  [NREQ-1:0]   request,
	input  [NREQ-1:0]   mask,
	output [NREQ-1:0]   grant,
	output              valid,
	output [NIDX-1:0]   index

);

// Encoded selected index

endmodule


module round_robin_arbiter #(
	
	parameter NREQ = 4,
	parameter NIDX = `CLOG2(NREQ),
	
	// time slots
	parameter SLOTW = 4,
	
) (
	
	input                    clk,
	input                    rst_n,
	input                    enable,
	input				     repleinish,
	input                    arbitrate,			// actively trigger arbitration
	
	// arbitration
	input  wire [NREQ-1:0]   request,
	input  wire [NREQ-1:0]   mask,
	output wire [NREQ-1:0]   grant,
	output                   valid,
	output wire [NIDX-1:0]   index
	output reg  [NREQ-1:0]   token;
	
	// slots control
	input  wire              load,
	input  wire [SLOTW-1:0]  amount,
	output reg               depleted			// slots of current round depleted
	
	
	
);


///////////////////////////////////////////////////////
// slots control
///////////////////////////////////////////////////////

localparam MAX_SLOT = 2**SLOTW-1;

// if needed we might have to implement a shadow slots register array
reg [SLOTW-1:0] default_slot;					// shadow slot register
reg [SLOTW-1:0] slot;


always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		default_slot <= MAX_SLOT;
	else begin
		if (load_slot)
			default_slot <= (amount < 1) ? 1 : amount;
		else
			default_slot <= default_slot;
	end
end


assign nxt_slots = (slots == 1) ? default_slot :

always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		slots[i] <= 1;
	else if
		slots[i] <= 1;
	else if (load & load_slot[i] & ~)
		slots[i] <= amount;
	else begin
		if (slot_enable)
			slots[i] <= nxt_slots[i];
		else
			slots[
	
	end
end
	


///////////////////////////////////////////////////////
// arbitration
///////////////////////////////////////////////////////

reg  [NREQ-1:0]  token;
wire             token_enable;


// mask incoming requests
wire [NREQ-1:0] mask_request = request & mask;
wire [NREQ-1:0] thermal_requet = mask_request & thermal_mask;	// requests masked by thermal decoded token


// mux between two priority mask to 
// generate valid and grant
wire mask_grant, thermal_grant;
wire mask_vld, thermal_vld;

leading_zero_detector #(
    .WIDTH(NREQ)
) thermal_mask_priority_arbiter (
    .in(thermal_request),
    .out(thermal_grant),
	.vld(thermal_vld)
);
leading_one_detector #(
    .WIDTH(NREQ)
) priority_arbiter (
    .in(mask_request),
    .out(mask_grant),
	.vld(mask_vld)
);

assign grant = ( |thermal_mask ) ? mask_grant    & {NREQ{enable}} & {NREQ{mask_vld}}   :
                                   thermal_grant & {NREQ{enable}} & {NREQ{thermal_vld}};

assign valid = mask_vld & thermal_vld & enable;
								   
// token & mask control

// updated token when actively triggered arbitrate or 
// current slots depleted or current requestor deasserted
wire token_enable = enable & 
                    (arbitrate | slot_depleted |);

always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		token <= 1;
	else if(repleinish)
		token <= 1;
	else begin
		if (token_enable)
			token <= grant;
		else
			token <= token;
	end
end

onehot2thermal #(
    .WIDTH(NREQ),
    .DIRECTION("LSB")
) (
    .in(token),
    .out(thermal_mask)
);

endmodule


module weighted_round_robin_arbiter #(

	parameter NREQ = 4,
	parameter NIDX = `CLOG2(NREQ),
	
	// time slots
	parameter MAX_SLOT = 8,
	parameter SLOTW = `CLOG2(MAX_SLOT),
	
	// weights
	parameter GWEIGHTW = 4,						// global weights
	parameter LWEIGHTW = 4,						// local weights
	
) (
	input               clk,
	input               rst_n,
	input               enable,
	
	
	// arbitration interface
	input  [NREQ-1:0]   request,
	input  [NREQ-1:0]   mask,
	output [NREQ-1:0]   grant,
	output              valid,
	output [NIDX-1:0]   index
	
	// weights interface
	
	
);



///////////////////////////////////////////////////////
// slots control
///////////////////////////////////////////////////////
reg [WEIGHTW-1:0] weights [NREQ-1:0];


genvar i;
generate
	for(i=0;  i< NREG; i=i+1) begin: weigth_ctrl
		
		always @(posedge clk or negedge rst_n) begin
			if (!rst_n)
				weights[i] <= 0;
			else begin
				if (load_weight)
					weights[i] <= weight;
				else
			end
		end
	
	end
endgenerate


endmodule



