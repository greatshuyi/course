
module cplx_mult_test();

// two complex number: X=-4+3i, Y=7-8i, both are 8 bit-width 2's numbers
// Z = X*Y = (-4*7-(3*-8)) + (3*7+4*8) ==>  ab = -28, cd = -24, adbc = 21+32 = 53;

wire [7:0] rex = 8'b1111_1100;
wire [7:0] imx = 8'b0000_0011;

wire [7:0] rey = 8'b0000_0111;
wire [7:0] imy = 8'b1111_1000;

// shift

wire signed [23:0] srex_s = $signed(rex) <<< 16;
wire signed [23:0] simx_s = $signed(imx);
wire signed [23:0] s_s    = srex_s + simx_s;

wire [23:0] srex = { rex         , {16{1'b0}} };
wire [23:0] simx = { {16{imx[7]}}, imx[7:0]   };
wire [23:0] s = srex + simx ;

wire signed [23:0] trey_s = $signed(rey) <<< 16;
wire signed [23:0] timy_s = $signed(imy);
wire signed [23:0] t_s    = trey_s + timy_s;

wire [23:0] trey = { rey         , {16{1'b0}} };
wire [23:0] timy = { {16{imy[7]}}, imy[7:0]   };
wire [23:0] t = trey + timy;

wire signed [48:0] w_s = s_s * t_s;
wire        [48:0] w = $signed(s) * $signed(t);

wire signed [15:0] bd_s   = w_s[15:0];
wire signed [15:0] adbc_s = w_s[16 +: 16];
wire signed [15:0] ac_s  = w >>> 32;

wire [15:0] bd   = w[15:0];
wire [16:0] adbc = w[16 +: 17];
wire [15:0] ac   = w[48 -: 16];

wire [16:0] re = ac + ~(bd) + 1;

initial begin
	$dumpvars;
	#20 $finish;
end


endmodule
