`ifndef __LIB_VH__


`define CLOG2(x) \
(x <= 2**1  ) ? 1  : \
(x <= 2**2  ) ? 2  : \
(x <= 2**3  ) ? 3  : \
(x <= 2**4  ) ? 4  : \
(x <= 2**5  ) ? 5  : \
(x <= 2**6  ) ? 6  : \
(x <= 2**7  ) ? 7  : \
(x <= 2**8  ) ? 8  : \
(x <= 2**9  ) ? 9  : \
(x <= 2**10 ) ? 10 : \
(x <= 2**11 ) ? 11 : \
(x <= 2**12 ) ? 12 : \
(x <= 2**13 ) ? 13 : \
(x <= 2**14 ) ? 14 : \
(x <= 2**15 ) ? 15 : \
(x <= 2**16 ) ? 16 : \
(x <= 2**17 ) ? 17 : \
(x <= 2**18 ) ? 18 : \
(x <= 2**19 ) ? 19 : \
(x <= 2**20 ) ? 20 : \
(x <= 2**21 ) ? 21 : \
(x <= 2**22 ) ? 22 : \
(x <= 2**23 ) ? 23 : \
(x <= 2**24 ) ? 24 : \
(x <= 2**25 ) ? 25 : \
-1



`define DFFR ( din, register ) \
always  @(posedge clk or negedge rst_n) begin \
	if (!rst_n) \
		register <= 0; \
	else \
		register <= din; \
end


`define DFFCR ( clear, din, register) \
always  @(posedge clk or negedge rst_n) begin \
	if (!rst_n) \
		register <= 0; \
	else if (clear) \
		register <= 0; \
	else \
		register <= din; \
end

`define DFFRE (enable, din, register) \
always  @(posedge clk or negedge rst_n) begin \cd -
	if (!rst_n) \
		register <= 0; \
	else begin \
		if (clear) \
			register <= 0; \
		else \
			register <= din; \
	end
end

`define DFFRCE (clear, enable, din, register) \
always  @(posedge clk or negedge rst_n) begin \
	if (!rst_n) \
		register <= 0; \
	else if (clear) \
		register <= 0; \
	else begin \
		if (enable) \
			register <= din; \
		else \
			register <= register; \
	end \
end


`endif
