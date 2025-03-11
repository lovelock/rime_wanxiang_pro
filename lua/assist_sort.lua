
--万象为了降低1位辅助码权重保证分词正常，因此在实践中将1-2位辅助码都是用abbrev来进行转写,这种会保证词库缺失词汇的情况下,不至于出现意外的靠拢,分不清辅助码还是下一个字的声母，
--但是有些时候单字超越了词组，如自然码中：jmma 睑 剑麻，于是调序 剑麻 睑 保证词组优先,并且我们在配置中巧妙的运用了/来send/1从而可以直接上屏 睑,从而减少一步按空格
--还会造成一个问题,但四码的时候如果词典里面没有这个词,abbrev就会派生出一些我们并不是特别想要的词汇,毕竟我们都收录了,这个时候我通过逻辑判断结合派生词的type标签sentence,严格控制在四码而且候选为第一候选,长度为2,通过滤镜删除了这个词
--保证了形如 forf直接出"佛",而不是"人佛".同时由于这个lua中各种判断和代码的逻辑,与分类归类及其重合,于是这个lua同样担负起了候选调序的功能,第一个是匹配1位或者2位辅助码让复合的字提前,这样在输入1位后很容易看到提示来输入第二位,有时更是唯一直接/上屏即可
--除了辅助码单字排序,还将英文候选\数字候选\自定义词组等等各种逻辑融合了起来,让中英混输以及lua生成候选单字\多字进行了有序的调节.
local M = {}
-- **获取辅助码**
function M.run_fuzhu(cand, env, initial_comment)
    local patterns = {
        moqi = "[^;]*;([^;]*);",
        flypy = "[^;]*;[^;]*;([^;]*);",
        zrm = "[^;]*;[^;]*;[^;]*;([^;]*);",
        jdh = "[^;]*;[^;]*;[^;]*;[^;]*;([^;]*);",
        cj = "[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;([^;]*);",
        tiger = "[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;([^;]*);",
        wubi = "[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;([^;]*);",
        hanxin = "[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;([^;]*)"
    }
    local pattern = patterns[env.settings.fuzhu_type]
    if not pattern then return {}, {} end  

    local full_fuzhu_list, first_fuzhu_list = {}, {}

    for segment in initial_comment:gmatch("[^%s]+") do
        local match = segment:match(pattern)
        if match then
            for sub_match in match:gmatch("[^,]+") do
                table.insert(full_fuzhu_list, sub_match)
                local first_char = sub_match:sub(1, 1)
                if first_char and first_char ~= "" then
                    table.insert(first_fuzhu_list, first_char)
                end
            end
        end
    end
    return full_fuzhu_list, first_fuzhu_list
end
-- **初始化**
function M.init(env)
    local config = env.engine.schema.config
    env.settings = {
        fuzhu_type = config:get_string("pro_comment_format/fuzhu_type") or ""
    }
end
-- **判断是否为字母或数字和特定符号**
local function is_alnum(text)
    return text:match("^[%w%s%.%-_%']+.*$") or text:match("^.*[%w%s%.%-_%']+$") ~= nil
end

-- **主逻辑**
-- **主逻辑**
function M.func(input, env)
    local input_code = env.engine.context.input
    local input_len = utf8.len(input_code)
    local candidates = {}

    -- 获取候选词并缓存
    for cand in input:iter() do
        table.insert(candidates, cand)
    end
    local first_cand = candidates[1]

    -- **如果输入码长 > 4，则直接输出默认排序**
    if input_len > 4 then
        for _, cand in ipairs(candidates) do yield(cand) end
        return
    end
    -- **如果第一个候选是字母/数字，则直接返回默认候选**
    if first_cand and is_alnum(first_cand.text) then
        for _, cand in ipairs(candidates) do yield(cand) end
        return
    end

    local noabbrev_cands, single_char_cands, alnum_cands, other_cands = {}, {}, {}, {}

    if input_len >= 3 and input_len <= 4 then
        -- **分类候选**
        for _, cand in ipairs(candidates) do
            -- 如果第一个候选符合特定条件则跳过
            if first_cand and utf8.len(first_cand.text) == 2 and first_cand.type == "sentence" and first_cand.text == cand.text then
                -- 也就是删除掉这个候选
            else
                table.insert(noabbrev_cands, cand)  -- 非删除候选加入 noabbrev_cands
            end
        end
        -- 继续分类其他类型的候选
        for _, cand in ipairs(candidates) do
            if is_alnum(cand.text) then
                table.insert(alnum_cands, cand)
            elseif utf8.len(cand.text) == 1 then
                table.insert(single_char_cands, cand)
            else
                table.insert(other_cands, cand)
            end
        end
        local last_char = input_code:sub(-1)
        local last_two = input_code:sub(-2)
        local has_match = false
        local moved, reordered = {}, {}

        -- **匹配和排序候选**
        if #other_cands == 0 then
            for _, cand in ipairs(single_char_cands) do
                table.insert(moved, cand)
                has_match = true
            end
        else
            for _, cand in ipairs(single_char_cands) do
                local full, first = M.run_fuzhu(cand, env, cand.comment or "")
                local matched = false

                if input_len == 4 then
                    for _, code in ipairs(full) do
                        if code == last_two then
                            matched = true
                            has_match = true
                            break
                        end
                    end
                else
                    for _, code in ipairs(first) do
                        if code == last_char then
                            matched = true
                            has_match = true
                            break
                        end
                    end
                end

                if matched then
                    table.insert(moved, cand)
                else
                    table.insert(reordered, cand)
                end
            end
        end
        -- **动态排序逻辑**
        if has_match then
            for _, v in ipairs(moved) do yield(v) end
            for _, v in ipairs(reordered) do yield(v) end
            for _, v in ipairs(alnum_cands) do yield(v) end
            for _, v in ipairs(other_cands) do yield(v) end
        else
            for _, v in ipairs(noabbrev_cands) do yield(v) end
            for _, v in ipairs(alnum_cands) do yield(v) end
            for _, v in ipairs(moved) do yield(v) end
            for _, v in ipairs(reordered) do yield(v) end
            for _, v in ipairs(other_cands) do yield(v) end
        end

    else  -- **处理 input_len < 3 的情况**
        single_char_cands, alnum_cands, other_cands = {}, {}, {}

        for _, cand in ipairs(candidates) do
            local len = utf8.len(cand.text)
            if is_alnum(cand.text) then
                table.insert(alnum_cands, cand)
            else
                table.insert(other_cands, cand)
            end
        end

        -- **按照既定顺序输出**
        for _, cand in ipairs(other_cands) do yield(cand) end
        for _, cand in ipairs(alnum_cands) do yield(cand) end
    end
end
return M