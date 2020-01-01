`timescale 1ns/1ns


module two_latent_grant();

reg clk;

parameter N= 8;

// picker stage

wire [N-1:0] complete;
wire grant;

reg [N-1:0] ready = 8'b10100101;

always @(posedge clk) begin
	if (grant)
		ready <= complete;
	else
		ready <= ready;
end


wire [N-1:0] picker;
wire [N-1:0] mask;

wire [N-1:0] request = ready & ~mask;


function [N-1:0] ldo;
	input [N-1:0] din;
	reg   [N-1:0] out;
	integer         i;
	begin
		out = {N{1'b0}};
		for(i = 0; i < N; i=i+1) begin
			if (din[i] == 1'b1) begin
				out = {N{1'b0}};
				out[i] = 1'b1;
			end
		end
		ldo = out;
	end
endfunction

assign picker = ldo(request);

wire valid = |(request);

// stage 1, the tricky here is 1, qualified pick

wire[N-1:0] picker_qual = picker & {N{valid}};

reg vld1 = 1'b0;
reg [N-1:0] picked1 = 8'b0;

always @(posedge clk) begin
	vld1 <= valid;
end


always @(posedge clk) begin
	picked1 <= picker_qual;
end
	
	
// stage 2


// fake grant
reg arb = 1'b0;


reg vld2 = 1'b0;
reg [N-1:0] picked2 = 8'b0;

always @(posedge clk) begin
	if (~vld2 | vld2 & arb)
		vld2 <= vld1;
	else
		vld2 <= vld2;

end


wire vld2_en = ~(vld1 & vld2 & ~arb);
always @(posedge clk) begin
	if (vld2_en )
		picked2 <= picked1;
	else
		picked2 <= picked2;
		
end


always @(posedge clk) begin
	if ( ($random % 2) == 0 )
		arb <= 1'b1;
	else
		arb <= 1'b0;

end

assign grant = arb;

assign complete = ready & ~picked2;

assign mask = vld2         ? picked2 :
              ~vld2 & vld1 ? picked1 : 8'b0;
			  
initial begin

	clk = 1'b0;
	forever #(5) clk = ~clk;

end

initial begin

	#(3000) $finish;

end


initial
        begin            
            $dumpfile("latent_grant.vcd");
            $dumpvars(0);
        end

endmodule




module three_latent_grant();

reg clk;

parameter N= 8;

// picker stage

wire [N-1:0] complete;
wire grant;

reg [N-1:0] ready = 8'b10100101;

always @(posedge clk) begin
	if (grant)
		ready <= complete;
	else
		ready <= ready;
end


wire [N-1:0] picker;
wire [N-1:0] mask;

wire [N-1:0] request = ready & ~mask;


function [N-1:0] ldo;
	input [N-1:0] din;
	reg   [N-1:0] out;
	integer         i;
	begin
		out = {N{1'b0}};
		for(i = 0; i < N; i=i+1) begin
			if (din[i] == 1'b1) begin
				out = {N{1'b0}};
				out[i] = 1'b1;
			end
		end
		ldo = out;
	end
endfunction

assign picker = ldo(request);

wire valid = |(request);

// stage 1, the tricky here is 1, qualified pick

wire[N-1:0] picker_qual = picker & {N{valid}};

reg vld1 = 1'b0;
reg [N-1:0] picked1 = 8'b0;

always @(posedge clk) begin
	vld1 <= valid;
end


always @(posedge clk) begin
	picked1 <= picker_qual;
end
	
	
// stage 2


// fake grant
reg arb = 1'b0;


reg vld2 = 1'b0;
reg [N-1:0] picked2 = 8'b0;

always @(posedge clk) begin
	if (~vld2 | vld2 & arb)
		vld2 <= vld1;
	else
		vld2 <= vld2;

end


wire vld2_en = ~(vld1 & vld2 & ~arb);
always @(posedge clk) begin
	if (vld2_en )
		picked2 <= picked1;
	else
		picked2 <= picked2;
		
end


always @(posedge clk) begin
	if ( ($random % 2) == 0 )
		arb <= 1'b1;
	else
		arb <= 1'b0;

end

assign grant = arb;

assign complete = ready & ~picked2 & {N{vld2}}{`;

assign mask =  vld2        ? picked2 :
              ~vld2 & vld1 ? picked1 : 8'b0;
			  
initial begin

	clk = 1'b0;
	forever #(5) clk = ~clk;

end

initial begin

	#(3000) $finish;

end


initial
        begin            
            $dumpfile("latent_grant.vcd");
            $dumpvars(0);
        end

endmodule
