local _db_pool = _db_pool or {}  -- 数据库池

-- 获取或创建 LevelDb 实例，避免重复打开
local function wrapLevelDb(dbname, mode)
    -- 检查数据库池是否已经包含该数据库
    _db_pool[dbname] = _db_pool[dbname] or LevelDb(dbname)
    local db = _db_pool[dbname]
    
    -- 如果数据库对象存在且未加载，打开数据库
    if db and not db:loaded() then
        if mode then
            db:open()  -- 打开数据库用于写入
        else
            db:open_read_only()  -- 只读模式打开数据库
        end
    end

    return db
end

local M = {}

-- 初始化词典并加载数据到 LevelDB
function M.init(env)
    local db = wrapLevelDb('tips', true)  -- 用于存储词典的 LevelDb 数据库，打开写入模式

    local path = rime_api.get_user_data_dir() .. "/jm_dicts/tips_show.txt"
    local file = io.open(path, "r")
    if not file then
        return
    end

    -- 从文本文件加载词典并写入到数据库
    for line in file:lines() do
        if string.sub(line, 1, 1) == "#" then goto continue end
        local value, key = line:match("([^\t]+)\t([^\t]+)/")
        if value and key then
            db:update(key, value)  -- 将词条写入数据库
        end
        ::continue::
    end
    file:close()
end

-- 处理候选词及提示逻辑
function M.func(input, env)
    local segment = env.engine.context.composition:back()

    local input_text = env.engine.context.input

    -- 从数据库中查询与输入文本匹配的词条
    local db = wrapLevelDb('tips', false)  -- 只读模式打开数据库
    local stick_phrase = db:fetch(input_text)

    local first_cand = nil
    local candidates = {}

    -- 收集候选词
    for cand in input:iter() do
        if not first_cand then
            first_cand = cand
        end
        table.insert(candidates, cand)
    end

    -- 匹配第一候选词
    local first_cand_match = first_cand and db:fetch(first_cand.text)

    -- 确定最终提示
    local tips = stick_phrase or first_cand_match
    if tips and tips ~= "" then
        segment.prompt = "〔" .. tips .. "〕"
    end

    -- 重新输出候选词
    for _, cand in ipairs(candidates) do
        yield(cand)
    end
end

return M
