-- ============================================================================
--  Neon Grid — Question Duel + roulette fix
--  Run after supabase_casino_v2.sql. Safe to re-run.
--
--  Two players, the same questions, chips on the line. Whoever answers wrong while the
--  other answers right hands over the pot. The server has to hold the answer key for that
--  to mean anything - otherwise each client simply claims it was right.
-- ============================================================================

-- ---------------------------------------------------------------- roulette fix
-- The old settle only touched rounds that had unpaid bets, so a round nobody bet on was
-- never written down and the wheel appeared frozen between players. Materialise the round
-- that just finished whenever anyone looks at the table.
create or replace function public.roulette_mark(round bigint)
returns void
language plpgsql security definer set search_path = public
as $$
declare p int;
begin
  if exists (select 1 from public.roulette_rounds where id = round) then return; end if;
  p := public.roulette_pocket(round);
  insert into public.roulette_rounds (id, pocket, colour, resolved_at)
       values (round, p, public.roulette_colour(p), now())
  on conflict (id) do nothing;
end $$;
revoke all on function public.roulette_mark(bigint) from public, anon, authenticated;

-- ---------------------------------------------------------------- answer key
-- One row, no policies: only the security-definer functions below can read it. If clients
-- could select from this table the duel would be a typing race with the answers on screen.
create table if not exists public.answer_key (
  id  int primary key,
  ans jsonb not null
);
alter table public.answer_key enable row level security;

insert into public.answer_key (id, ans) values (1, '{"0":["C"],"1":["C"],"2":["C"],"3":["D"],"4":["A"],"5":["C"],"6":["D"],"7":["D"],"8":["A"],"9":["B"],"10":["A"],"11":["D"],"12":["C","D"],"13":["C"],"14":["A"],"15":["A"],"16":["B"],"17":["B"],"18":["D"],"19":["D"],"20":["B"],"21":["A"],"22":["D"],"23":["B","C"],"24":["A"],"25":["D"],"26":["B"],"27":["B"],"28":["C"],"29":["A","C"],"30":["D"],"31":["D"],"32":["C"],"33":["D"],"34":["A"],"35":["C"],"36":["A"],"37":["A"],"38":["C"],"39":["B"],"40":["B"],"41":["D"],"42":["C"],"43":["A"],"44":["D"],"45":["B"],"46":["D"],"47":["A","E"],"48":["A"],"49":["A"],"50":["C"],"51":["B"],"52":["A"],"53":["A","B"],"54":["A"],"55":["D"],"56":["B"],"57":["B"],"58":["A"],"59":["D"],"60":["A"],"61":["A"],"62":["B"],"63":["B"],"64":["A"],"65":["B"],"66":["A"],"67":["A","E"],"68":["B"],"69":["D"],"70":["B"],"71":["B"],"72":["B"],"73":["D"],"74":["C"],"75":["A"],"76":["C"],"77":["A"],"78":["A"],"79":["A"],"80":["C"],"81":["C"],"82":["A"],"83":["D"],"84":["B"],"85":["D"],"86":["D"],"87":["C"],"88":["B"],"89":["B"],"90":["D","E"],"91":["B"],"92":["D"],"93":["A"],"94":["A"],"95":["D"],"96":["D"],"97":["D"],"98":["A"],"99":["C"],"100":["D"],"101":["C"],"102":["A"],"103":["B"],"104":["A","C"],"105":["B"],"106":["B"],"107":["B"],"108":["D"],"109":["C"],"110":["A"],"111":["D"],"112":["C"],"113":["A"],"114":["D"],"115":["D"],"116":["D"],"117":["D"],"118":["C"],"119":["D"],"120":["D"],"121":["A"],"122":["A","C"],"123":["A"],"124":["D"],"125":["A"],"126":["D"],"127":["C"],"128":["A"],"129":["B"],"130":["D"],"131":["B"],"132":["A"],"133":["D"],"134":["C"],"135":["C"],"136":["B","C"],"137":["C","E"],"138":["B"],"139":["C"],"140":["A","C"],"141":["D"],"142":["C","E"],"143":["A"],"144":["A"],"145":["C"],"146":["B"],"147":["C"],"148":["D","E"],"149":["A"],"150":["A"],"151":["B","E"],"152":["B"],"153":["C"],"154":["C"],"155":["B"],"156":["C"],"157":["A"],"158":["A"],"159":["D"],"160":["A"],"161":["B"],"162":["A","B"],"163":["A"],"164":["C"],"165":["C","E"],"166":["B"],"167":["D"],"168":["B"],"169":["A"],"170":["B"],"171":["B"],"172":["D"],"173":["D"],"174":["D"],"175":["C"],"176":["B"],"177":["A","B"],"178":["A"],"179":["A"],"180":["A"],"181":["B"],"182":["A"],"183":["D"],"184":["A"],"185":["B"],"186":["D"],"187":["B"],"188":["B"],"189":["A"],"190":["D"],"191":["D"],"192":["A"],"193":["A"],"194":["A","E"],"195":["D"],"196":["C"],"197":["C"],"198":["B","D"],"199":["B"],"200":["D"],"201":["C"],"202":["A"],"203":["D"],"204":["A"],"205":["B"],"206":["B"],"207":["D"],"208":["C"],"209":["B","E"],"210":["D"],"211":["B"],"212":["B"],"213":["C"],"214":["A"],"215":["A","D"],"216":["C"],"217":["A"],"218":["A"],"219":["D"],"220":["C","E"],"221":["B"],"222":["B"],"223":["A"],"224":["B"],"225":["D"],"226":["C"],"227":["C"],"228":["B"],"229":["A"],"230":["C"],"231":["C"],"232":["D"],"233":["A"],"234":["B"],"235":["C"],"236":["A"],"237":["D"],"238":["D"],"239":["B"],"240":["A"],"241":["A"],"242":["A"],"243":["A"],"244":["D"],"245":["A"],"246":["D"],"247":["C"],"248":["C"],"249":["A"],"250":["B"],"251":["A"],"252":["C"],"253":["A"],"254":["D"],"255":["B"],"256":["B"],"257":["D"],"258":["D"],"259":["C","E"],"260":["A","D"],"261":["C"],"262":["C"],"263":["A"],"264":["C"],"265":["C"],"266":["D"],"267":["A"],"268":["D"],"269":["D"],"270":["D"],"271":["A","D"],"272":["D"],"273":["A","C"],"274":["C"],"275":["C"],"276":["A","C"],"277":["C"],"278":["D"],"279":["B"],"280":["B"],"281":["C"],"282":["D"],"283":["D"],"284":["A"],"285":["A","D"],"286":["A"],"287":["B"],"288":["B"],"289":["D"],"290":["D"],"291":["A"],"292":["A"],"293":["A"],"294":["C"],"295":["C"],"296":["B"],"297":["A"],"298":["B"],"299":["D"],"300":["A"],"301":["C"],"302":["A"],"303":["B"],"304":["C"],"305":["B"],"306":["C"],"307":["D"],"308":["B"],"309":["D","E"],"310":["D"],"311":["D"],"312":["B"],"313":["B"],"314":["A"],"315":["A"],"316":["B","E"],"317":["B","D"],"318":["B"],"319":["C","E"],"320":["B"],"321":["C"],"322":["A"],"323":["B"],"324":["D"],"325":["D"],"326":["C"],"327":["D"],"328":["B"],"329":["A"],"330":["A"],"331":["C"],"332":["C"],"333":["A","E"],"334":["A","E"],"335":["D"],"336":["B"],"337":["B"],"338":["C"],"339":["B"],"340":["D"],"341":["A","D"],"342":["A"],"343":["A"],"344":["A"],"345":["C"],"346":["D"],"347":["C"],"348":["C"],"349":["B"],"350":["C"],"351":["A"],"352":["C"],"353":["C"],"354":["B","C"],"355":["B"],"356":["B"],"357":["D"],"358":["A","C","D"],"359":["B"],"360":["D"],"361":["A"],"362":["A"],"363":["A"],"364":["B"],"365":["B","E"],"366":["C"],"367":["B"],"368":["B"],"369":["B","D","F"],"370":["D"],"371":["C"],"372":["A"],"373":["B"],"374":["A"],"375":["C"],"376":["C"],"377":["B"],"378":["B"],"379":["A"],"380":["D"],"381":["A"],"382":["A"],"383":["B"],"384":["B","C","D"],"385":["C"],"386":["D"],"387":["D"],"388":["A"],"389":["A"],"390":["A"],"391":["D"],"392":["B"],"393":["C"],"394":["C"],"395":["A","D"],"396":["D"],"397":["B","D"],"398":["A"],"399":["C","D"],"400":["C"],"401":["D"],"402":["A","C"],"403":["A"],"404":["A","B"],"405":["A"],"406":["A","B"],"407":["C"],"408":["A"],"409":["B"],"410":["A","D"],"411":["A"],"412":["B"],"413":["A"],"414":["D"],"415":["C"],"416":["B"],"417":["D"],"418":["D"],"419":["C"],"420":["B","C","E"],"421":["D"],"422":["A"],"423":["B"],"424":["D"],"425":["B"],"426":["C"],"427":["B"],"428":["C"],"429":["D"],"430":["B"],"431":["A"],"432":["C"],"433":["D"],"434":["A"],"435":["C"],"436":["B"],"437":["B"],"438":["D"],"439":["B"],"440":["A","C"],"441":["B"],"442":["C"],"443":["A"],"444":["A"],"445":["B"],"446":["B"],"447":["D"],"448":["D"],"449":["B"],"450":["C"],"451":["D"],"452":["A","C","E"],"453":["D"],"454":["A"],"455":["A"],"456":["A"],"457":["B"],"458":["B"],"459":["C"],"460":["D"],"461":["B"],"462":["A"],"463":["C"],"464":["C"],"465":["C"],"466":["B"],"467":["A"],"468":["C"],"469":["A"],"470":["C"],"471":["A","E"],"472":["C"],"473":["C"],"474":["C"],"475":["D"],"476":["A"],"477":["A"],"478":["D"],"479":["D"],"480":["D"],"481":["D"],"482":["A"],"483":["D"],"484":["A"],"485":["D"],"486":["C"],"487":["D"],"488":["D"],"489":["A"],"490":["D"],"491":["A"],"492":["B"],"493":["C"],"494":["C"],"495":["C"],"496":["D"],"497":["A"],"498":["A"],"499":["A","B"],"500":["D","E","F"],"501":["A","C"],"502":["D"],"503":["A","C"],"504":["C"],"505":["A"],"506":["D"],"507":["A"],"508":["A","C"],"509":["A"],"510":["B"],"511":["A"],"512":["A"],"513":["B"],"514":["A"],"515":["B"],"516":["C"],"517":["A"],"518":["C"],"519":["C"],"520":["B"],"521":["C"],"522":["A","E"],"523":["C"],"524":["A"],"525":["C"],"526":["C"],"527":["C"],"528":["B","D"],"529":["C"],"530":["A"],"531":["A"],"532":["A"],"533":["D"],"534":["D"],"535":["D"],"536":["C"],"537":["D"],"538":["A"],"539":["A"],"540":["A"],"541":["A"],"542":["D"],"543":["C"],"544":["A"],"545":["C"],"546":["B"],"547":["B"],"548":["C"],"549":["D"],"550":["A","B"],"551":["A"],"552":["A","C"],"553":["D"],"554":["B"],"555":["C"],"556":["C","D","F"],"557":["D"],"558":["B","E"],"559":["C"],"560":["D"],"561":["A"],"562":["A","B"],"563":["D"],"564":["D"],"565":["A"],"566":["D"],"567":["C"],"568":["A"],"569":["A","C"],"570":["C"],"571":["C"],"572":["A"],"573":["A"],"574":["A"],"575":["A"],"576":["A"],"577":["A"],"578":["C"],"579":["B"],"580":["D"],"581":["B"],"582":["D"],"583":["B"],"584":["B"],"585":["B"],"586":["A"],"587":["D"],"588":["B"],"589":["C"],"590":["C"],"591":["B"],"592":["C"],"593":["C","E"],"594":["C"],"595":["A"],"596":["D"],"597":["A"],"598":["D"],"599":["D"],"600":["C"],"601":["A"],"602":["C"],"603":["C"],"604":["A"],"605":["D"],"606":["B","E"],"607":["A"],"608":["C","D"],"609":["C"],"610":["B"],"611":["B","E"],"612":["A"],"613":["D","E"],"614":["D"],"615":["C","D"],"616":["D"],"617":["A","E"],"618":["A"],"619":["C"],"620":["B"],"621":["D"],"622":["D"],"623":["D"],"624":["C"],"625":["C"],"626":["A","C"],"627":["A"],"628":["C"],"629":["B"],"630":["D"],"631":["C"],"632":["A"],"633":["C"],"634":["C"],"635":["A"],"636":["D"],"637":["D"],"638":["B"],"639":["B"],"640":["D"],"641":["A"],"642":["A"],"643":["B"],"644":["D"],"645":["A"],"646":["A","D"],"647":["D"],"648":["D"],"649":["C"],"650":["D"],"651":["D"],"652":["A"],"653":["C"],"654":["A"],"655":["C"],"656":["B"],"657":["A","B"],"658":["C"],"659":["C"],"660":["A"],"661":["B"],"662":["B"],"663":["D"],"664":["C"],"665":["C"],"666":["B"],"667":["C"],"668":["C"],"669":["D"],"670":["A"],"671":["C"],"672":["C"],"673":["D"],"674":["D"],"675":["C"],"676":["A"],"677":["C"],"678":["A"],"679":["B"],"680":["A","B","D"],"681":["D"],"682":["C"],"683":["A"],"684":["A"],"685":["D"],"686":["D"],"687":["C"],"688":["A"],"689":["C"],"690":["C"],"691":["A","C"],"692":["C"],"693":["B","E"],"694":["D"],"695":["D"],"696":["C"],"697":["A"],"698":["B"],"699":["A"],"700":["C"],"701":["A"],"702":["A"],"703":["C","D"],"704":["D"],"705":["A"],"706":["B"],"707":["B","C"],"708":["B","C"],"709":["A"],"710":["D"],"711":["D"],"712":["A"],"713":["C"],"714":["C"],"715":["D"],"716":["B"],"717":["D"],"718":["D"],"719":["D"],"720":["A","C","F"],"721":["A"],"722":["C"],"723":["C"],"724":["B"],"725":["D"],"726":["D"],"727":["B"],"728":["B"],"729":["A"],"730":["B"],"731":["D"],"732":["A"],"733":["B","E"],"734":["C"],"735":["A"],"736":["A"],"737":["D"],"738":["C"],"739":["C"],"740":["C"],"741":["A"],"742":["C"],"743":["D"],"744":["A","E"],"745":["D"],"746":["A"],"747":["B"],"748":["C"],"749":["A"],"750":["C"],"751":["B"],"752":["D"],"753":["D"],"754":["A"],"755":["D"],"756":["D"],"757":["B"],"758":["D"],"759":["B"],"760":["C"],"761":["B"],"762":["D"],"763":["A","B"],"764":["B"],"765":["A"],"766":["B","D"],"767":["D"],"768":["A"],"769":["D"],"770":["B"],"771":["B"],"772":["D"],"773":["B"],"774":["B"],"775":["D"],"776":["D"],"777":["A"],"778":["B","E","F"],"779":["D"],"780":["B"],"781":["B"],"782":["B"],"783":["C"],"784":["A"],"785":["B","E","F"],"786":["D"],"787":["B"],"788":["C"],"789":["C"],"790":["B"],"791":["A"],"792":["D"],"793":["B"],"794":["B"],"795":["B"],"796":["A"],"797":["A"],"798":["B"],"799":["C","D"],"800":["B"],"801":["D"],"802":["C"],"803":["D"],"804":["A"],"805":["D"],"806":["B"],"807":["D"],"808":["C"],"809":["A","D"],"810":["B"],"811":["A"],"812":["A"],"813":["D"],"814":["B"],"815":["A"],"816":["D"],"817":["D"],"818":["D"],"819":["C"],"820":["D"],"821":["C"],"822":["B"],"823":["D"],"824":["D"],"825":["A"],"826":["C","D"],"827":["D"],"828":["C"],"829":["A"],"830":["C"],"831":["D"],"832":["C"],"833":["D"],"834":["B"],"835":["B"],"836":["A"],"837":["A"],"838":["B"],"839":["A"],"840":["C"],"841":["A"],"842":["B"],"843":["C"],"844":["B"],"845":["B"],"846":["C"],"847":["D"],"848":["D"],"849":["B"],"850":["D"],"851":["D"],"852":["B"],"853":["A"],"854":["A"],"855":["A"],"856":["B"],"857":["D"],"858":["A"],"859":["C"],"860":["A"],"861":["C"],"862":["B","E"],"863":["A","E"],"864":["A"],"865":["D"],"866":["C"],"867":["A"],"868":["B","C"],"869":["A"],"870":["C"],"871":["B"],"872":["B"],"873":["A"],"874":["D"],"875":["C"],"876":["A"],"877":["C"],"878":["C"],"879":["A"],"880":["C"],"881":["A","D"],"882":["B"],"883":["A"],"884":["C"],"885":["A"],"886":["B"],"887":["C"],"888":["D"],"889":["C"],"890":["D"],"891":["B"],"892":["C"],"893":["C"],"894":["B"],"895":["B"],"896":["C"],"897":["C"],"898":["D"],"899":["B"],"900":["C"],"901":["C"],"902":["C"],"903":["A"],"904":["B"],"905":["D"],"906":["B"],"907":["A"],"908":["B","C"],"909":["B"],"910":["B"],"911":["C"],"912":["A"],"913":["D"],"914":["B"],"915":["B","E"],"916":["D"],"917":["D"],"918":["B"],"919":["A"],"920":["A"],"921":["B"],"922":["A"],"923":["B"],"924":["A","E"],"925":["A"],"926":["A"],"927":["C"],"928":["C"],"929":["A"],"930":["B"],"931":["D"],"932":["C"],"933":["B"],"934":["D","E","F"],"935":["B"],"936":["D"],"937":["C"],"938":["C"],"939":["A"],"940":["C"],"941":["C"],"942":["C"],"943":["A","E","F"],"944":["A"],"945":["B"],"946":["C"],"947":["A"],"948":["D"],"949":["B","D","E"],"950":["B"],"951":["B"],"952":["B","E"],"953":["B"],"954":["A"],"955":["C"],"956":["B"],"957":["A"],"958":["C"],"959":["B"],"960":["A"],"961":["D"],"962":["B"],"963":["B","E"],"964":["C","D"],"965":["C"],"966":["B"],"967":["B"],"968":["B"],"969":["B"],"970":["C"],"971":["A"],"972":["A"],"973":["D"],"974":["D"],"975":["D"],"976":["A"],"977":["D"],"978":["B"],"979":["B"],"980":["D"],"981":["D"],"982":["A"],"983":["B"],"984":["D"],"985":["D"],"986":["C"],"987":["B"],"988":["B"],"989":["D"],"990":["C"],"991":["D"],"992":["A"],"993":["D"],"994":["D"],"995":["A"],"996":["D"],"997":["A"],"998":["B"],"999":["D"],"1000":["C"],"1001":["A"],"1002":["D"],"1003":["C"],"1004":["A","D"],"1005":["C","E","F"],"1006":["B"],"1007":["B"],"1008":["A"],"1009":["A"],"1010":["A"],"1011":["A"],"1012":["D"],"1013":["C"],"1014":["A"],"1015":["D"],"1016":["B"],"1017":["B"],"1018":["A"],"1019":["A"],"1020":["B","C","E"],"1021":["B"],"1022":["D"],"1023":["D"],"1024":["B"],"1025":["C"],"1026":["C"],"1027":["A"],"1028":["C"],"1029":["B"],"1030":["C"],"1031":["A"],"1032":["D"],"1033":["C"],"1034":["A"],"1035":["D"],"1036":["B"],"1037":["A"],"1038":["B"],"1039":["D"],"1040":["C"],"1041":["C"],"1042":["D"],"1043":["A","C","E"],"1044":["C"],"1045":["A"],"1046":["D"],"1047":["D"],"1048":["A"],"1049":["A"],"1050":["A"],"1051":["C"],"1052":["A"],"1053":["C"],"1054":["B"],"1055":["C"],"1056":["C"],"1057":["C"],"1058":["D"],"1059":["A"],"1060":["D"],"1061":["D"],"1062":["A"],"1063":["C"],"1064":["D"],"1065":["D"],"1066":["D"],"1067":["A"],"1068":["C"],"1069":["D"],"1070":["A"],"1071":["B","C","D"],"1072":["D"],"1073":["A"],"1074":["C"],"1075":["A"],"1076":["A"],"1077":["B"],"1078":["D"],"1079":["D"],"1080":["D"],"1081":["A"],"1082":["D"],"1083":["C"],"1084":["C"],"1085":["D","E"],"1086":["A"],"1087":["B"],"1088":["C"],"1089":["D"],"1090":["B"],"1091":["A"],"1092":["B"],"1093":["C"],"1094":["A"],"1095":["A"],"1096":["B"],"1097":["B"],"1098":["A"],"1099":["B"],"1100":["B"],"1101":["D"],"1102":["D"],"1103":["C"],"1104":["A","C"],"1105":["B"],"1106":["B","D"],"1107":["C"],"1108":["B"],"1109":["B"],"1110":["B"],"1111":["C"],"1112":["B","D"],"1113":["D"],"1114":["C","D"],"1115":["D"],"1116":["A"],"1117":["C"],"1118":["A","C"],"1119":["B"],"1120":["A"],"1121":["A"],"1122":["C"],"1123":["B"],"1124":["B"],"1125":["D"],"1126":["A"],"1127":["A"],"1128":["D"],"1129":["B"],"1130":["B"],"1131":["D"],"1132":["C"],"1133":["D"],"1134":["D"],"1135":["D"],"1136":["D"],"1137":["A","D"],"1138":["D"],"1139":["A","E"],"1140":["C","D"],"1141":["A"],"1142":["B"],"1143":["B"],"1144":["C"],"1145":["D"],"1146":["A"],"1147":["B"],"1148":["C"],"1149":["B"],"1150":["D"],"1151":["C"],"1152":["A","D"],"1153":["C"],"1154":["D"],"1155":["C"],"1156":["A"],"1157":["A"],"1158":["D"],"1159":["B"],"1160":["C"],"1161":["B"],"1162":["C"],"1163":["C"],"1164":["A"],"1165":["C"],"1166":["C"],"1167":["B"],"1168":["D"],"1169":["A"],"1170":["C"],"1171":["C","D"],"1172":["A","B","F"],"1173":["C"],"1174":["D"],"1175":["B"],"1176":["A"],"1177":["D"],"1178":["C"],"1179":["A","C"],"1180":["A"],"1181":["C"],"1182":["A"],"1183":["C"],"1184":["D"],"1185":["C"],"1186":["A"],"1187":["D"],"1188":["A","C"],"1189":["B"],"1190":["A"],"1191":["A"],"1192":["D"],"1193":["A"],"1194":["C"],"1195":["B","E"],"1196":["C"],"1197":["B","D"],"1198":["A"],"1199":["B"],"1200":["A"]}'::jsonb)
on conflict (id) do update set ans = excluded.ans;

-- ---------------------------------------------------------------- duels
create table if not exists public.duels (
  id         uuid primary key default gen_random_uuid(),
  stake      bigint not null check (stake > 0),
  a          uuid not null references auth.users (id) on delete cascade,
  b          uuid references auth.users (id) on delete cascade,
  a_name     text,
  b_name     text,
  status     text not null default 'waiting',      -- waiting | active | done
  q_ids      int[] not null default '{}',
  turn       int not null default 0,
  a_pick     text[], b_pick text[],
  a_ok       boolean, b_ok boolean,
  a_score    int not null default 0,
  b_score    int not null default 0,
  winner     uuid,
  reason     text,
  turn_start timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists duels_status_idx on public.duels (status, stake);
alter table public.duels enable row level security;

-- you can read a duel you are in, or one that is waiting for an opponent
drop policy if exists "read own duels" on public.duels;
create policy "read own duels" on public.duels
  for select using (auth.uid() = a or auth.uid() = b or status = 'waiting');

-- ---------------------------------------------------------------- helpers
-- How long each question is open. Scenario questions run to a hundred words plus four
-- long options, so 30 seconds was not enough time to read one, let alone think.
create or replace function public.duel_seconds() returns int
language sql immutable as $$ select 75; $$;
create or replace function public.duel_answers(qid int)
returns text[]
language plpgsql security definer set search_path = public
as $$
declare j jsonb;
begin
  select ans -> qid::text into j from public.answer_key where id = 1;
  if j is null then return null; end if;
  return array(select jsonb_array_elements_text(j));
end $$;
revoke all on function public.duel_answers(int) from public, anon, authenticated;

-- what the caller is allowed to see: never the opponent's pick before you have answered
create or replace function public.duel_view(d public.duels)
returns jsonb
language plpgsql stable set search_path = public
as $$
declare me uuid := auth.uid(); iam_a boolean; mine text[]; theirs text[]; answered boolean;
begin
  iam_a := (d.a = me);
  mine   := case when iam_a then d.a_pick else d.b_pick end;
  theirs := case when iam_a then d.b_pick else d.a_pick end;
  answered := mine is not null;
  return jsonb_build_object(
    'id', d.id, 'status', d.status, 'stake', d.stake, 'turn', d.turn,
    'question', case when d.status = 'active' then d.q_ids[d.turn + 1] else null end,
    'you',      jsonb_build_object('name', case when iam_a then d.a_name else d.b_name end,
                                   'score', case when iam_a then d.a_score else d.b_score end,
                                   'answered', answered),
    'them',     jsonb_build_object('name', case when iam_a then d.b_name else d.a_name end,
                                   'score', case when iam_a then d.b_score else d.a_score end,
                                   -- only that they answered, never what they chose
                                   'answered', theirs is not null),
    'secondsTotal', public.duel_seconds(),
    'secondsLeft', case when d.status = 'active' and d.turn_start is not null
                        then greatest(0, public.duel_seconds()
                                          - round(extract(epoch from (now() - d.turn_start))))::int
                        else null end,
    'winner', d.winner, 'reason', d.reason,
    'youWon', (d.winner is not null and d.winner = me));
end $$;

-- ---------------------------------------------------------------- queue
create or replace function public.duel_find(stake bigint)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; d public.duels; nm text; ids int[];
begin
  w := public.wallet_row();
  if duel_find.stake <= 0 then raise exception 'stake must be positive'; end if;
  if w.chips < duel_find.stake then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;

  -- already in something? hand it back rather than starting a second one
  select * into d from public.duels
   where (a = auth.uid() or b = auth.uid()) and status in ('waiting','active')
   order by created_at desc limit 1;
  if d.id is not null then
    return jsonb_build_object('ok', true, 'duel', public.duel_view(d), 'chips', w.chips);
  end if;

  select username into nm from public.profiles where id = auth.uid();
  nm := coalesce(nm, 'player');

  -- take a seat at someone else's table if one is open at this stake.
  -- the column and the parameter are both called "stake", so both sides are qualified:
  -- dd.stake is the row, duel_find.stake is the argument.
  select * into d from public.duels dd
   where dd.status = 'waiting' and dd.stake = duel_find.stake and dd.a <> auth.uid()
   order by dd.created_at limit 1
   for update skip locked;

  if d.id is not null then
    -- a set-returning function in the select list combined with order by/limit behaves
    -- unpredictably; expand the keys first, then sample from them
    select array_agg(k) into ids from (
      select key::int as k
        from jsonb_object_keys((select ans from public.answer_key where id = 1)) as key
       order by random()
       limit 5
    ) s;
    update public.duels
       set b = auth.uid(), b_name = nm, status = 'active', q_ids = ids,
           turn = 0, turn_start = now(), updated_at = now()
     where id = d.id returning * into d;
    update public.wallets set chips = chips - duel_find.stake, updated_at = now()
     where user_id = auth.uid();
  else
    insert into public.duels (stake, a, a_name, status)
         values (duel_find.stake, auth.uid(), nm, 'waiting') returning * into d;
    update public.wallets set chips = chips - duel_find.stake, updated_at = now()
     where user_id = auth.uid();
  end if;

  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 'duel', public.duel_view(d), 'chips', w.chips);
end $$;

-- ---------------------------------------------------------------- play
create or replace function public.duel_state(duel uuid)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare d public.duels; w public.wallets;
begin
  w := public.wallet_row();
  select * into d from public.duels where id = duel and (a = auth.uid() or b = auth.uid());
  if d.id is null then return jsonb_build_object('ok', false, 'reason', 'no such duel'); end if;

  -- a player who walks away forfeits once the clock runs out
  if d.status = 'active' and d.turn_start is not null
     and now() - d.turn_start > (public.duel_seconds() || ' seconds')::interval then
    if d.a_pick is null and d.b_pick is not null then
      d := public.duel_finish(d, d.b, 'opponent ran out of time');
    elsif d.b_pick is null and d.a_pick is not null then
      d := public.duel_finish(d, d.a, 'opponent ran out of time');
    elsif d.a_pick is null and d.b_pick is null then
      d := public.duel_next(d);                      -- neither answered: move on
    end if;
  end if;

  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 'duel', public.duel_view(d), 'chips', w.chips);
end $$;

create or replace function public.duel_finish(d public.duels, win uuid, why text)
returns public.duels
language plpgsql security definer set search_path = public
as $$
declare cur public.duels;
begin
  -- Both players poll duel_state, so two calls can decide the same duel is over at the same
  -- moment. Without taking the row first, each would pay the pot out and the pair would walk
  -- away with more chips than they staked.
  select * into cur from public.duels where id = d.id for update;
  if cur.id is null then return d; end if;
  if cur.status = 'done' then return cur; end if;
  d := cur;

  if win is not null then
    update public.wallets set chips = chips + d.stake * 2,
           lifetime_won = lifetime_won + d.stake, updated_at = now()
     where user_id = win;
    update public.wallets set lifetime_lost = lifetime_lost + d.stake, updated_at = now()
     where user_id = case when win = d.a then d.b else d.a end;
  else                                                -- draw: both stakes returned
    update public.wallets set chips = chips + d.stake where user_id in (d.a, d.b);
  end if;
  update public.duels set status = 'done', winner = win, reason = why, updated_at = now()
   where id = d.id and status <> 'done' returning * into d;
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (d.a, 'duel', d.stake,
               case when win = d.a then d.stake when win is null then 0 else -d.stake end,
               jsonb_build_object('reason', why));
  return d;
end $$;
revoke all on function public.duel_finish(public.duels, uuid, text) from public, anon, authenticated;

create or replace function public.duel_next(d public.duels)
returns public.duels
language plpgsql security definer set search_path = public
as $$
begin
  if d.turn + 1 >= array_length(d.q_ids, 1) then
    if    d.a_score > d.b_score then return public.duel_finish(d, d.a, 'higher score');
    elsif d.b_score > d.a_score then return public.duel_finish(d, d.b, 'higher score');
    else  return public.duel_finish(d, null, 'draw');
    end if;
  end if;
  update public.duels
     set turn = turn + 1, a_pick = null, b_pick = null, a_ok = null, b_ok = null,
         turn_start = now(), updated_at = now()
   where id = d.id returning * into d;
  return d;
end $$;
revoke all on function public.duel_next(public.duels) from public, anon, authenticated;

create or replace function public.duel_answer(duel uuid, picks text[])
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare d public.duels; correct text[]; ok boolean; iam_a boolean; w public.wallets;
begin
  select * into d from public.duels where id = duel and (a = auth.uid() or b = auth.uid());
  if d.id is null or d.status <> 'active' then
    return jsonb_build_object('ok', false, 'reason', 'not in an active duel');
  end if;
  iam_a := (d.a = auth.uid());
  if (iam_a and d.a_pick is not null) or (not iam_a and d.b_pick is not null) then
    return jsonb_build_object('ok', true, 'duel', public.duel_view(d));   -- already answered
  end if;

  correct := public.duel_answers(d.q_ids[d.turn + 1]);
  ok := correct is not null
        and array_length(picks, 1) = array_length(correct, 1)
        and picks @> correct and correct @> picks;

  if iam_a then
    update public.duels set a_pick = picks, a_ok = ok,
           a_score = a_score + (case when ok then 1 else 0 end), updated_at = now()
     where id = d.id returning * into d;
  else
    update public.duels set b_pick = picks, b_ok = ok,
           b_score = b_score + (case when ok then 1 else 0 end), updated_at = now()
     where id = d.id returning * into d;
  end if;

  -- both in: one right and one wrong ends it there, which is the whole point of the mode
  if d.a_pick is not null and d.b_pick is not null then
    if d.a_ok and not d.b_ok then
      d := public.duel_finish(d, d.a, 'opponent answered wrong');
    elsif d.b_ok and not d.a_ok then
      d := public.duel_finish(d, d.b, 'opponent answered wrong');
    else
      d := public.duel_next(d);
    end if;
  end if;

  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 'duel', public.duel_view(d), 'chips', w.chips);
end $$;

create or replace function public.duel_leave(duel uuid)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare d public.duels;
begin
  select * into d from public.duels where id = duel and (a = auth.uid() or b = auth.uid());
  if d.id is null then return jsonb_build_object('ok', false); end if;
  if d.status = 'waiting' then                        -- nobody joined: refund and drop it
    update public.wallets set chips = chips + d.stake where user_id = d.a;
    delete from public.duels where id = d.id;
  elsif d.status = 'active' then                      -- walking out of a live duel concedes
    perform public.duel_finish(d, case when d.a = auth.uid() then d.b else d.a end, 'opponent left');
  end if;
  return jsonb_build_object('ok', true);
end $$;

-- ---------------------------------------------------------------- retention
create or replace function public.casino_sweep()
returns void
language plpgsql security definer set search_path = public
as $$
begin
  delete from public.roulette_bets   where created_at < now() - interval '2 hours';
  delete from public.roulette_rounds where created_at < now() - interval '2 hours';
  delete from public.casino_log      where created_at < now() - interval '7 days';
  delete from public.bj_hands        where state = 'done' and updated_at < now() - interval '1 day';
  delete from public.duels           where status = 'done'    and updated_at < now() - interval '1 day';
  delete from public.duels           where status = 'waiting' and created_at < now() - interval '10 minutes';
  delete from public.duels           where status = 'active'  and updated_at < now() - interval '1 hour';
end $$;

-- ---------------------------------------------------------------- permissions
do $$
declare f text;
begin
  foreach f in array array['duel_find(bigint)','duel_state(uuid)','duel_answer(uuid,text[])',
                           'duel_leave(uuid)','duel_seconds()']
  loop
    execute format('revoke all on function public.%s from public, anon;', f);
    execute format('grant execute on function public.%s to authenticated;', f);
  end loop;
end $$;

notify pgrst, 'reload schema';

-- ---------------------------------------------------------------- verify
-- expect: 1 key row, 1201 questions in it, and the duel functions present
select (select count(*) from public.answer_key) as key_rows,
       (select count(*) from jsonb_object_keys((select ans from public.answer_key where id = 1))) as questions,
       (select count(*) from pg_proc where proname in
          ('duel_find','duel_state','duel_answer','duel_leave')) as duel_functions;
