/*
    Grant Geyer
    Spring 2021
    This records all RAM accesses along with the time.
*/

`include "cpu_types_pkg.vh"
import cpu_types_pkg::*;

module ram_tracker (
    input logic CLK,
    input logic nRST,
    input ramstate_t ramstate,
    input logic ramREN,
    input logic ramWEN,
    input word_t ramaddr,
    input word_t ramstore,
    input word_t ramload
);

    integer fptr;
    string output_str;

    initial begin : INIT_FILE
        fptr = $fopen("ram_trace.log", "w");
    end

    always_ff @ (posedge CLK) begin
        if(ramstate == ACCESS) begin
            if(ramREN) begin
                $sformat(output_str, "Time: %0d ns: RAM read  at %X  of word %X\n", $time / 1000, ramaddr, ramload);
            end else if (ramWEN) begin
                $sformat(output_str, "Time: %0d ns: RAM write at %X for data %X\n", $time / 1000, ramaddr, ramload);
            end else begin
                $sformat(output_str, "");
            end
            $fwrite(fptr, output_str);
        end
    end

    final begin : CLOSE_FILE
        $fclose(fptr);
    end

endmodule