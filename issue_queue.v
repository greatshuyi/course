module issue_queue #(

	parameter DW = 16,
	parameter 

) (

	input clk;
	input 
	
	input wire repleinish,
	
	// credit
	output reg credit,
	
	
	// sender side
	input                put,
	input wire [0 +: DW] din,
	
	
	
	

	// reciever side
	input ack_vld,
	input ack_cancel,
	
	output wire req,
	output wire [0 +: DW] data,
	input wire gnt,

);


wire safe_put, safe_get;


///////////////////////////////////////////////////////
// credit control
///////////////////////////////////////////////////////

// Once repleinish asserted, send credit count






endmodule
