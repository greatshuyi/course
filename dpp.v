

module DFFE #(

	parameter W = 8,

) (
	input wire         clk,
	input wire         en,
	input wire [W-1:0] in,
	output reg [W-1:0] out
);

always @(posedge clk) begin
	if (en)
		out <= in;
	else
		out <= out;
end


endmodule


module DFF #(
	parameter W = 1,
) (
	input wire         clk,
	input wire         rst_n,
	input wire [W-1:0] in,
	output reg [W-1:0] out
);

always @(posedge clk or negedge rst_n) begin
	if (!rst_n)
		out <= 1'b0;
	else
		out <= in;
end


endmodule




module dpp (
	input wire clk,
	input wire rst_n,
	input wire in_vld,
	input wire frm_sync,
	input wire [35:0] in_dat,
	
	output wire out_vld,
	output wire [127:0] out_dat
);

//---------------------------------------------------------
// pre stage
//---------------------------------------------------------

wire        stage0_in_vld;
wire        stage0_frm_vld;
wire [35:0] stage0_pld;


DFF #(.W(2+36)) ff_stage0_in_vld (
	.clk ( clk ),
	.rst_n ( rst_n ),
	.in  ( {in_vld, 
	        frm_vld,
			in_dat} ),
	.out ( {stage0_in_vld, 
	        stage0_frm_vld,
			stage0_pld} )
);

wire        stage0_vld;	// TODO: implement me


//---------------------------------------------------------
// stage 1
//---------------------------------------------------------


wire stage0_qual_vld;

wire [2:0] cnt
wire [3:0] cnt_ns;

wire [8:0] symbol0;
wire [8:0] symbol1;
wire [8:0] symbol2;
wire [8:0] symbol3;

assign {symbol0, symbol1, symbol2, symbol3} = stage0_pld & {128{stage0_qual_vld}};

wire [3:0] rsvd = 4'h5;

// k bit-map

wire [3:0] map = {symbol0[8], symbol1[8], symbol2[8], symbol3[8]};
wire any_k = |map;
wire [1:0]   = amy_k ? 2'b10 : 2'b01;




wire       stage1_vld;
wire [1:0] sh;
wire [7:0] byte0;
wire [7:0] byte1;
wire [7:0] byte2;
wire [7:0] byte3;


DFF #(.W(1)) ff_stage1_vld (
	.clk ( clk ),
	.rst_n ( rst_n ),
	.in  ( stage0_qual_vld ),
	.out ( stage1_vld )
);


DFFE #(.W(2+4*8+3)) ff_stage1_pld (
	.clk( clk ),
	.en ( stage0_qual_vld ),
	.in ( { sh_ns, encode0, encode1, encode2, encode3, cnt_ns} ),
	.out( { sh   , byte0,   byte1,   byte2,   byte3,   cnt   } ) 
);




//---------------------------------------------------------
// stage 2
//---------------------------------------------------------


wire [15:0] i0_ns = qam_lkup(byte0[7:4]);
wire [15:0] i1_ns = qam_lkup(byte1[7:4]);
wire [15:0] i2_ns = qam_lkup(byte2[7:4]);
wire [15:0] i3_ns = qam_lkup(byte3[7:4]);
wire [15:0] q0_ns = qam_lkup(byte0[3:0]);
wire [15:0] q1_ns = qam_lkup(byte1[3:0]);
wire [15:0] q2_ns = qam_lkup(byte2[3:0]);
wire [15:0] q3_ns = qam_lkup(byte3[3:0]);


wire [15:0] i0;
wire [15:0] i1;
wire [15:0] i2;
wire [15:0] i3;
wire [15:0] q0;
wire [15:0] q1;
wire [15:0] q2;
wire [15:0] q3;



wire [11:0] factor_im0;
wire [11:0] factor_im1;
wire [11:0] factor_im2;
wire [11:0] factor_im3;
wire [11:0] factor_re0;
wire [11:0] factor_re1;
wire [11:0] factor_re2;
wire [11:0] factor_re3;









//---------------------------------------------------------
// final stage
//---------------------------------------------------------

wire [15:0] im0;
wire [15:0] im1;
wire [15:0] im2;
wire [15:0] im3;
wire [15:0] re0;
wire [15:0] re1;
wire [15:0] re2;
wire [15:0] re3;


DFF #(.W(1)) ff_stage_vld (
	.clk ( clk ),
	.rst_n ( rst_n ),
	.in  ( stage2_vld ),
	.out ( out_vld )
);


assign out_dat = {im0, re0,
                  im1, re1,
				  im2, re2,
				  im3, re3};

//DFFE #(.W()) ff_stage2_pld (
//	.clk( clk ),
//	.en ( stage2_vld ),
//	.in ( { im0, re0, im1, re1, im2, re2, im3, re3 } ),
//	.out( out_dat ) 
//);
	



//---------------------------------------------------------
// common function
//---------------------------------------------------------


function [3:0] k_compress_lkup;
	input [7:0] din;
	
	reg [3:0] out;
	
	begin
		
		case(din):
			8'b00011100: out = 4'b0000;
			8'b00111100: out = 4'b0001;
			8'b01011100: out = 4'b0010;
			8'b01111100: out = 4'b0011;
			8'b10011100: out = 4'b0100;
			8'b10111100: out = 4'b0101;
			8'b11011100: out = 4'b0110;
			8'b11111100: out = 4'b0111;
			8'b11110111: out = 4'b1011;
			8'b11111011: out = 4'b1010;
			8'b11111101: out = 4'b1001;
			8'b11111110: out = 4'b1000;
			default:	 out = 4'b0000;
		endcase
	
        k_compress_lkup = out;

	end
endfunction
	
function [31:0] qam_lkup;

    input [3:0] din;

    begin

        case(din):
            4'h0: qam_lkup = 16'hf6cc;
            4'h1: qam_lkup = 16'hf806;
            4'h2: qam_lkup = 16'hfa7a;
            4'h3: qam_lkup = 16'hf940;
            4'h4: qam_lkup = 16'hff63;
            4'h5: qam_lkup = 16'hfe29;
            4'h6: qam_lkup = 16'hfbb4;
            4'h7: qam_lkup = 16'hfcef;
            4'h8: qam_lkup = 16'h0934;
            4'h9: qam_lkup = 16'h07fa;
            4'ha: qam_lkup = 16'h0586;
            4'hb: qam_lkup = 16'h06c0;
            4'hc: qam_lkup = 16'h009d;
            4'hd: qam_lkup = 16'h01d7;
            4'he: qam_lkup = 16'h044c;
            4'hf: qam_lkup = 16'h0311;
        endcase

    end

endfunction


endmodule
