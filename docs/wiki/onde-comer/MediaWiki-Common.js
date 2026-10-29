/* MediaWiki:Common.js — https://pedalhidrografi.co/wiki/MediaWiki:Common.js
 * Fonte versionada: github.com/pedalhidro/amora, docs/wiki/onde-comer/.
 *
 * Mapas do Kartographer (<mapframe>, <maplink>) com a cara do Pedal:
 *  1. Topografia colorida por cima do OpenStreetMap, a 50 % (o amora usa 85 %;
 *     aqui mais transparente, pra ler as ruas do OSM por baixo).
 *     Os tiles vêm DIRETO do bucket (storage.googleapis.com/telhas): o CSP do
 *     Miraheze libera esse host em img-src, mas não telhas.pedalhidrografi.co.
 *     Custa egress do GCS por tile (sem a Cloudflare na frente) — irrelevante
 *     no tráfego do wiki. Se o Miraheze liberar telhas no CSP, troque a URL.
 *  2. Marcadores como bolinhas. O Kartographer daqui desenha os pinos com
 *     <servidor de mapas>/v4/marker/…png, e o servidor configurado
 *     (tile.openstreetmap.org) não tem esse serviço: sem isto, todo ponto vira
 *     imagem quebrada. A cor é a "marker-color" da feição.
 * O Kartographer avisa cada mapa pronto pelo hook wikipage.maps — o do artigo
 * (lista de mapas) e o de tela cheia (um mapa só), que é OUTRA instância.
 */
( function () {
	var TOPO_URL = 'https://storage.googleapis.com/telhas/rmsampa-v2/{z}/{x}/{y}.png';
	var DEFAULT_COLOR = '#d9480f';

	function dotIcon( L, color ) {
		if ( !/^#?[0-9a-f]{3,8}$/i.test( color || '' ) ) { color = DEFAULT_COLOR; }
		if ( color.charAt( 0 ) !== '#' ) { color = '#' + color; }
		return L.divIcon( {
			className: 'ph-map-dot',
			html: '<span style="display:block;width:14px;height:14px;border-radius:50%;' +
				'background:' + color + ';border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.45)"></span>',
			iconSize: [ 18, 18 ],
			iconAnchor: [ 9, 9 ],
			popupAnchor: [ 0, -9 ]
		} );
	}

	function restyleMarkers( L, layer ) {
		if ( !layer || !layer.eachLayer ) { return; }
		layer.eachLayer( function ( child ) {
			if ( child instanceof L.Marker ) {
				var props = ( child.feature && child.feature.properties ) || {};
				child.setIcon( dotIcon( L, props[ 'marker-color' ] ) );
			} else {
				restyleMarkers( L, child );
			}
		} );
	}

	function decorate( map ) {
		var L = window.L;
		if ( !L || !map || map._phDecorated ) { return; }
		map._phDecorated = true;
		L.tileLayer( TOPO_URL, {
			maxZoom: 19,
			maxNativeZoom: 16,
			opacity: 0.5,
			attribution: 'Topografia: <a href="https://amora.pedalhidrografi.co">Pedal Hidrográfico</a>'
		} ).addTo( map );
		map.eachLayer( function ( layer ) { restyleMarkers( L, layer ); } );
		map.on( 'layeradd', function ( ev ) { restyleMarkers( L, ev.layer ); } );
	}

	mw.hook( 'wikipage.maps' ).add( function ( maps ) {
		( Array.isArray( maps ) ? maps : [ maps ] ).forEach( function ( map ) {
			if ( map && map.doWhenReady ) {
				map.doWhenReady( function () { decorate( map ); } );
			} else {
				decorate( map );
			}
		} );
	} );
}() );
