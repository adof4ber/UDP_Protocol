-- Lua script to recognize the DataTransferProtocolAdo protocol (DTPA) with ports 1070 and 1069
-- Ensure this script is added to Wireshark's plugins directory

local dtpa_proto = Proto("DTPA", "Data Transfer Protocol Ado")

-- Define fields in the protocol header
local f_msg_type = ProtoField.uint8("dtpa.msg_type", "Message Type", base.DEC)
local f_fragment_id = ProtoField.uint16("dtpa.fragment_id", "Fragment ID", base.DEC)
local f_total_fragments = ProtoField.uint16("dtpa.total_fragments", "Total Fragments", base.DEC)
local f_crc = ProtoField.uint16("dtpa.crc", "CRC", base.HEX)

-- Register the fields
dtpa_proto.fields = {f_msg_type, f_fragment_id, f_total_fragments, f_crc}

-- Message type mapping
local msg_types = {
    [0] = "SYN",
    [1] = "SYN-ACK",
    [2] = "ACK",
    [3] = "DATA",
    [4] = "NACK",
    [5] = "KEEP-ALIVE",
    [6] = "FILE METADATA",
    [7] = "FILE DATA",
    [8] = "CLOSE INIT",
    [9] = "CLOSE ACK",
    [10] = "CLOSE FINAL",
    [11] = "END"
}

-- Dissector function
function dtpa_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "DTPA"

    if buffer:len() < 8 then
        return  -- Packet too short for header
    end

    local subtree = tree:add(dtpa_proto, buffer(), "DTPA Protocol Data")

    -- Parse the header fields
    local msg_type = buffer(0, 1):uint()
    local fragment_id = buffer(1, 2):uint()
    local total_fragments = buffer(3, 2):uint()
    local crc = buffer(5, 2):uint()
    local data = buffer(7):string()

    -- Add fields to the protocol tree
    subtree:add(f_msg_type, buffer(0, 1)):append_text(" (" .. (msg_types[msg_type] or "Unknown") .. ")")
    subtree:add(f_fragment_id, buffer(1, 2))
    subtree:add(f_total_fragments, buffer(3, 2))
    subtree:add(f_crc, buffer(5, 2))

    -- Display data payload if present
    if data and #data > 0 then
        subtree:add(buffer(7), "Payload: " .. data)
    end

    -- Add color rules (indirect method)
    if msg_type == 0 then
        pinfo.cols.info:set("SYN")
        -- You can set a color rule in Wireshark for dtpa.msg_type == 0 (SYN)
    elseif msg_type == 1 then
        pinfo.cols.info:set("SYN-ACK")
        -- You can set a color rule in Wireshark for dtpa.msg_type == 1 (SYN-ACK)
    elseif msg_type == 2 then
        pinfo.cols.info:set("ACK")
        -- You can set a color rule in Wireshark for dtpa.msg_type == 2 (ACK)
    end
end

-- Add the dissector to the specified ports
local udp_table = DissectorTable.get("udp.port")
udp_table:add(1070, dtpa_proto)
udp_table:add(1069, dtpa_proto)
