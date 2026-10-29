-- Módulo:Onde comer — https://pedalhidrografi.co/wiki/Módulo:Onde_comer
--
-- Lugares para comer indicados por quem pedala. Cada lugar é UMA chamada de
-- {{Lugar para comer}} na página "Onde comer"; este módulo:
--   * lugar(frame) — desenha a ficha do lugar (nome, endereço, tipo,
--     bicicleta, links de mapa) e um <maplink> com o ponto;
--   * mapa(frame)  — lê o wikitexto da PRÓPRIA página, junta todas as chamadas
--     de {{Lugar para comer}} (com a região = a seção "== ... ==" onde estão)
--     e desenha UM <mapframe> com todos os pontos.
-- O mapa lê a página em vez de usar group/show do Kartographer porque esses
-- atributos só existem no "modo Wikivoyage", desligado aqui. Efeito colateral:
-- na pré-visualização o mapa mostra a versão SALVA (a ficha já mostra o novo).
--
-- CONTRATO com o amora (camada "Onde comer" em amora.pedalhidrografi.co, que
-- lê estes pontos pela API: action=query&prop=mapdata): as propriedades das
-- feições — id, nome, regiao, endereco, metro, tipo, bicicleta, instagram,
-- site, aproximado — são lidas lá. Mudou aqui, mude lá. Fonte versionada:
-- docs/wiki/onde-comer/ no repo github.com/pedalhidro/amora.
local p = {}

local TEMPLATE = 'lugar para comer'
local COR = '#d9480f'
local AMORA = 'https://amora.pedalhidrografi.co/#comer='
local SIM = { sim = true, s = true, ['1'] = true, ['true'] = true, yes = true }
local COMBINING = '[' .. mw.ustring.char(0x300) .. '-' .. mw.ustring.char(0x36F) .. ']'

local function trim(s)
	if s == nil then return '' end
	return mw.text.trim(tostring(s))
end

-- Primeiro parâmetro não vazio entre os nomes dados (aceita com e sem acento).
local function pick(args, ...)
	for _, k in ipairs({ ... }) do
		local v = trim(args[k])
		if v ~= '' then return v end
	end
	return nil
end

-- Wikitexto → texto corrido (pro amora e pros popups do mapa).
local function plain(s)
	if not s then return nil end
	s = s:gsub('<!%-%-.-%-%->', '')
	s = s:gsub('%[%[[^%]|]-|([^%]]-)%]%]', '%1')
	s = s:gsub('%[%[([^%]]-)%]%]', '%1')
	s = s:gsub('%[https?://%S+%s+([^%]]-)%]', '%1')
	s = s:gsub('%[(https?://[^%]%s]+)%]', '%1')
	s = s:gsub("'''", ''):gsub("''", '')
	s = s:gsub('<[^>]->', '')
	s = mw.text.trim(s)
	if s == '' or s:match('^%(a preencher%)$') then return nil end
	return s
end

-- "-23.546, -46.642" (como o Google Maps copia), "-23.546 -46.642" ou
-- lat= / lon= separados. Aceita o sinal de menos tipográfico (−).
local function coords(args)
	local lat = tonumber(pick(args, 'lat', 'latitude') or '')
	local lon = tonumber(pick(args, 'lon', 'long', 'longitude') or '')
	if not (lat and lon) then
		local c = pick(args, 'coordenadas', 'coords')
		if c then
			c = c:gsub('−', '-')
			local a, b = c:match('^(%-?[%d.]+)[%s,;]+(%-?[%d.]+)$')
			lat, lon = tonumber(a or ''), tonumber(b or '')
		end
	end
	if lat and lon and lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180 then
		return lat, lon
	end
	return nil
end

-- "@perfil", "perfil" ou o link inteiro do perfil.
local function instagram(v)
	if not v then return nil end
	local h = v:match('instagram%.com/([%w._]+)')
	if not h then h = v:gsub('^@', '') end
	if h:match('^[%w._]+$') then return h end
	return nil
end

-- Identificador estável do lugar (âncora na página e #comer= no amora).
local function slug(s)
	s = mw.ustring.gsub(mw.ustring.toNFD(plain(s) or s), COMBINING, '')
	s = s:lower():gsub("['’]", ''):gsub('[^a-z0-9]+', '-'):gsub('^%-+', ''):gsub('%-+$', '')
	return s
end

local function feature(args, regiao)
	local nome = pick(args, 'nome')
	if not nome then return nil end
	local lat, lon = coords(args)
	local site = pick(args, 'site')
	if site and not site:match('^https?://') then site = nil end
	local props = {
		id = slug(nome),
		title = plain(nome) or nome,
		-- o Kartographer passa title/description por wikitexto→HTML ("&" vira
		-- "&amp;"); nome é o mesmo texto cru, pro amora.
		nome = plain(nome) or nome,
		regiao = plain(regiao),
		endereco = plain(pick(args, 'endereço', 'endereco')),
		metro = plain(pick(args, 'metrô', 'metro')),
		tipo = plain(pick(args, 'tipo')),
		bicicleta = plain(pick(args, 'bicicleta')),
		instagram = instagram(pick(args, 'instagram')),
		site = site,
		aproximado = SIM[mw.ustring.lower(pick(args, 'aproximado') or '')] or nil,
		['marker-color'] = COR,
		['marker-size'] = 'medium',
		['marker-symbol'] = 'restaurant',
	}
	local desc = {}
	if props.tipo then desc[#desc + 1] = props.tipo end
	if props.bicicleta then desc[#desc + 1] = '🚲 ' .. props.bicicleta end
	if props.endereco then desc[#desc + 1] = props.endereco end
	if #desc > 0 then props.description = table.concat(desc, '<br>') end
	local f = { type = 'Feature', properties = props }
	if lat then f.geometry = { type = 'Point', coordinates = { lon, lat } } end
	return f
end

function p.lugar(frame)
	local args = frame:getParent().args
	local f = feature(args)
	if not f then
		return '<strong class="error">{{Lugar para comer}}: falta o parâmetro <code>nome</code>.</strong>'
	end
	local P = f.properties
	local nome = pick(args, 'nome')
	local q = { P.title }
	if P.endereco then q[#q + 1] = P.endereco end
	q[#q + 1] = 'São Paulo'
	local gmaps = 'https://www.google.com/maps/search/?api=1&query=' .. mw.uri.encode(table.concat(q, ', '), 'QUERY')

	local out = {}
	out[#out + 1] = string.format('<h3 id="%s">[%s %s]</h3>', P.id, gmaps, nome)

	local linha = { "* '''Endereço:''' " .. (pick(args, 'endereço', 'endereco') or "''(a preencher)''") }
	if P.metro then linha[1] = linha[1] .. ' (metrô ' .. pick(args, 'metrô', 'metro') .. ')' end
	if P.instagram then
		linha[#linha + 1] = string.format('[https://www.instagram.com/%s/ @%s]', P.instagram, P.instagram)
	end
	if P.site then linha[#linha + 1] = '[' .. P.site .. ' site]' end
	out[#out + 1] = table.concat(linha, ' · ')
	out[#out + 1] = "* '''Tipo:''' " .. (pick(args, 'tipo') or "''(a preencher)''")
	out[#out + 1] = "* '''Bicicleta:''' " .. (pick(args, 'bicicleta') or "''(a preencher)''")

	if f.geometry then
		local lon, lat = f.geometry.coordinates[1], f.geometry.coordinates[2]
		local ml = frame:extensionTag('maplink', mw.text.jsonEncode(f), {
			text = 'ver no mapa', zoom = '16',
			latitude = string.format('%.6f', lat), longitude = string.format('%.6f', lon),
		})
		out[#out + 1] = "* '''Mapa:''' " .. ml
			.. (P.aproximado and " ''(posição aproximada)''" or '')
			.. ' · [' .. AMORA .. P.id .. ' no amora]'
	else
		out[#out + 1] = "* '''Mapa:''' ''sem coordenadas ainda — [[#Como sugerir um lugar|como adicionar]]''"
	end
	return table.concat(out, '\n')
end

-- Varre o wikitexto atrás das chamadas da predefinição. Devolve
-- { {args = {...}, regiao = '...'}, ... } na ordem da página.
local function collect(text)
	-- Exemplos em <pre>/<nowiki> e comentários não são lugares.
	text = text:gsub('<!%-%-.-%-%->', '')
	for _, tag in ipairs({ 'pre', 'nowiki', 'syntaxhighlight' }) do
		text = text:gsub('<' .. tag .. '[^>]*>.-</' .. tag .. '>', '')
	end

	local headings, pos = {}, 1
	for line in (text .. '\n'):gmatch('([^\n]*)\n') do
		local h = line:match('^==%s*([^=].-)%s*==%s*$')
		if h then headings[#headings + 1] = { pos = pos, text = h } end
		pos = pos + #line + 1
	end
	local function regionAt(at)
		local r
		for _, h in ipairs(headings) do
			if h.pos < at then r = h.text else break end
		end
		return r
	end

	local found, i, n = {}, 1, #text
	while true do
		local s = text:find('{{', i, true)
		if not s then break end
		-- casa as chaves; '|' só separa no nível de cima e fora de [[...]]
		local depth, sq, j, last, parts = 0, 0, s, s + 2, {}
		local stop
		while j <= n do
			local two = text:sub(j, j + 1)
			if two == '{{' then depth = depth + 1; j = j + 2
			elseif two == '}}' then
				depth = depth - 1
				if depth == 0 then parts[#parts + 1] = text:sub(last, j - 1); stop = j + 2; break end
				j = j + 2
			elseif two == '[[' then sq = sq + 1; j = j + 2
			elseif two == ']]' then sq = math.max(0, sq - 1); j = j + 2
			elseif depth == 1 and sq == 0 and text:sub(j, j) == '|' then
				parts[#parts + 1] = text:sub(last, j - 1); last = j + 1; j = j + 1
			else j = j + 1 end
		end
		if not stop then break end
		local name = trim(parts[1]):gsub('_', ' '):gsub('^[Pp]redefinição:', ''):gsub('^[Tt]emplate:', '')
		if mw.ustring.lower(name) == TEMPLATE then
			local args = {}
			for k = 2, #parts do
				local key, val = parts[k]:match('^%s*([^=]-)%s*=(.*)$')
				if key then args[key] = trim(val) end
			end
			found[#found + 1] = { args = args, regiao = regionAt(s) }
			i = stop
		else
			i = s + 2
		end
	end
	return found
end

-- {{Mapa onde comer|altura=420}} — um mapa com todos os lugares da página.
function p.mapa(frame)
	local pargs = frame:getParent() and frame:getParent().args or {}
	local title = mw.title.getCurrentTitle()
	local feats = {}
	for _, it in ipairs(collect(title:getContent() or '')) do
		local f = feature(it.args, it.regiao)
		if f and f.geometry then feats[#feats + 1] = f end
	end
	local attrs = {
		width = 'full',
		height = pick(pargs, 'altura') or '420',
		align = 'center',
		text = #feats .. ' lugares · fundo: Topografia colorida do Pedal Hidrográfico',
	}
	if #feats == 0 then
		attrs.latitude, attrs.longitude, attrs.zoom = '-23.55', '-46.64', '12'
		attrs.text = 'Nenhum lugar com coordenadas ainda.'
	end
	return frame:extensionTag('mapframe', mw.text.jsonEncode({ type = 'FeatureCollection', features = feats }), attrs)
end

return p
