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
    [6] = "KEEP-ALIVE-ACK",
    [7] = "FILE METADATA",
    [8] = "FILE DATA",
    [9] = "CLOSE INIT",
    [10] = "CLOSE ACK",
    [11] = "CLOSE FINAL",
    [12] = "END"
}

-- Dissector function
function dtpa_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "DTPA"

    if buffer:len() < 8 then
        return  
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

    -- Set Info column based on message type
    if msg_types[msg_type] then
        pinfo.cols.info:set(msg_types[msg_type])
    else
        pinfo.cols.info:set("Unknown Message Type")
    end
end

-- Add the dissector to the specified ports
local udp_table = DissectorTable.get("udp.port")
udp_table:add(1070, dtpa_proto)
udp_table:add(1069, dtpa_proto)
