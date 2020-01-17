
module cplx_mult_test();

// two complex number: X=-4+3i, Y=7-8i, both are 8 bit-width 2's numbers
// Z = X*Y = (-4*7-(3*-8)) + (3*7+4*8) ==>  ab = -28, cd = -24, adbc = 21+32 = 53;

//wire [7:0] rex = 8'b1111_1100;
//wire [7:0] imx = 8'b0000_0011;
//
//wire [7:0] rey = 8'b0000_0111;
//wire [7:0] imy = 8'b1111_1000;
//
//// shift
//
//wire signed [23:0] srex_s = $signed(rex) <<< 16;
//wire signed [23:0] simx_s = $signed(imx);
//wire signed [23:0] s_s    = srex_s + simx_s;
//
//wire [23:0] srex = { rex         , {16{1'b0}} };
//wire [23:0] simx = { {16{imx[7]}}, imx[7:0]   };
//wire [23:0] s = srex + simx ;
//
//wire signed [23:0] trey_s = $signed(rey) <<< 16;
//wire signed [23:0] timy_s = $signed(imy);
//wire signed [23:0] t_s    = trey_s + timy_s;
//
//wire [23:0] trey = { rey         , {16{1'b0}} };
//wire [23:0] timy = { {16{imy[7]}}, imy[7:0]   };
//wire [23:0] t = trey + timy;
//
//wire signed [48:0] w_s = s_s * t_s;
//wire        [48:0] w = $signed(s) * $signed(t);
//
//wire signed [15:0] bd_s   = w_s[15:0];
//wire signed [15:0] adbc_s = w_s[16 +: 16];
//wire signed [15:0] ac_s  = w >>> 32;
//
//wire [15:0] bd   = w[15:0];
//wire [16:0] adbc = w[16 +: 17];
//wire [15:0] ac   = w[48 -: 16];
//
//wire [16:0] re = ac + ~(bd) + 1;

reg clk;

reg  signed  [7:0] multa = 55;
reg  signed  [7:0] multb = 66;
wire [15:0] res;


assign res = multa * multb;

wire a_all_zero = multa[7:4] == 4'b0000;
wire a_all_one  = multa[7:4] == 4'b1111;

wire b_all_zero = multb[7:4] == 4'b0000;
wire b_all_one  = multb[7:4] == 4'b1111;

wire [3:0] trunc_multa = ( a_all_zero | a_all_one ) ? 4'b0000 : multa[7:4];
wire [3:0] i_multa = trunc_multa;
//wire [7:0] ii_multa = {trunc_multa, 4'b0000};
wire       a_sign = a_all_one ? 1'b1 : 1'b0;
wire [4:0] f_multa = {a_sign,   multa[3:0]};
local
all_
wire [3:0] trunc_multb = ( b_all_zero | b_all_one ) ? 4'b0000 : multb[7:4];
wire [3:0] i_multb = trunc_multb;
//wire [7:0] ii_multb = {trunc_multb, 4'b0000};
wire       b_sign = b_all_one ? 1'b1 : 1'b0;
wire [4:0] f_multb = {b_sign,   multb[3:0]};

wire [7:0] ac = $signed(i_multa) * $signed(i_multb);
wire [8:0] ad = $signed(i_multa) * $signed(f_multb);
wire [8:0] cb = $signed(i_multb) * $signed(f_multa);
wire [9:0] bd = $signed(f_multa) * $signed(f_multb);

wire [15:0] ac_s = {ac, 8'b0};
wire [12:0] ad_s = {ad, 4'b0};
wire [12:0] cb_s = {cb, 4'b0};

wire [15:0] res_g = $signed(ac_s) + $signed(ad_s) + $signed(cb_s) + $signed(bd);


//wire [11:0] res_i = multb * $signed(i_multa);
//wire [13:0] res_f = multb * $signed(f_multa);
//wire [15:0] res_ii = {res_i, 4'b0000};
//wire [15:0] res_g = $signed(res_ii) + $signed(res_f);
//wire [15:0] res_g = res_ii + res_f;			// totally wrong

always @(posedge clk) begin
	multa <= $random % 256;
	multb <= $random % 256;
end

always @(negedge clk) begin
	if (res_g != res ) begin
		$display("@time %t, split mismatch, expected %h, calc %h", $time, res, res_g);
	end
end
 

initial begin
	$dumpvars;
	#20000 $finish;
end

initial begin
	clk = 1'b0;	
	forever #1 clk = ~clk;
end


endmodule
