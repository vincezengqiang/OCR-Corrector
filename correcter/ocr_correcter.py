#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Title   : OCR纠错服务
@File    :   ocr_correcter.py
@Author  : Tian
@Time    : 2020/06/16 5:04 下午
@Version : 1.0
"""
import re
from abc import ABCMeta, abstractmethod
import logging
from correcter.utils.char_sim import CharFuncs

logger = logging.getLogger(__name__)

class CorrecterConfig:
    prob_threshold = 0.9
    similarity_threshold = 0.6
    key_words_file = 'data/kwds_credit_report.txt'
    char_meta_file = 'data/char_meta.txt'

class BaseCorrecter(metaclass=ABCMeta):
    """
    纠错的基类
    """
    def __init__(self, config):
        self.config = config
        self.char_sim = CharFuncs(config.char_meta_file)
        self.regulars = self.compile_regulars()


    def correct(self, texts, probs=None):

        # 前处理
        if probs:
            texts2correct, mask2process, texts_pass = self.preprocess(texts, probs)
        else:
            texts2correct, mask2process, texts_pass = self.preprocess_non_prob(texts)
        if not texts2correct:
            logger.info('没有需要纠错的文本')
            return texts
        # 纠错
        after_correct = self.correct_all(texts2correct, mask2process)
        # 后处理
        after_correct = self.post_process(after_correct, texts_pass)

        return after_correct

    @abstractmethod
    def correct_all(self, texts, mask):
        pass

    def preprocess(self, texts, probs):
        text2process = []
        text_pass = []
        mask2process = []
        logger.info('共有【%d】条文本', len(texts))

        for i, (sent, p) in enumerate(zip(texts, probs)):
            if not self.do_correct_filter(sent):
                # 全数字、全英文等情况不需要纠错
                text_pass.append((i, sent))
            else:
                mask = self.prob2mask(p)
                # prob高于阈值，不需要纠错
                if not any(mask):
                    text_pass.append((i, sent))
                # 需要纠错
                else:
                    logger.debug('【%s】需要纠错：%r', sent, [(_s, _p) for _s, _p, _m in zip(sent, p, mask) if _m])
                    text2process.append(sent)
                    mask2process.append(mask)
        logger.info('需要纠错【%d】条', len(text2process))

        return text2process, mask2process, text_pass

    def preprocess_non_prob(self, texts):
        text2process = []
        mask2process = []
        text_pass = []
        for i, sent in enumerate(texts):
            if not self.do_correct_filter(sent):
                # 全数字、全英文等情况不需要纠错
                text_pass.append((i, sent))
            else:
                text2process.append(sent)
                mask2process.append([True]*len(sent))

        return text2process, mask2process, text_pass

    @staticmethod
    def post_process(results,text_pass):
        if text_pass:
            for i,s in text_pass:
                results.insert(i,s)

        return results

    def do_correct_filter(self, text):
        """
        过滤是否纠错；在子类中可能需要被重写
        :param text
        :param mask
        :return: True for do, False for not
        """
        # 小于2个汉字的文本不纠错
        if len(re.findall(self.regulars['chinese'], text)) < 2:
            return False
        return True


    def probs2mask(self, probs):
        """
        >>> cr = BaseCorrecter(CorrecterConfig)
        >>> cr.probs2mask([[0.99,0.85,1.00],[0.53,1.0]])
        '[[0,1,0],[1,0]]'
        """
        masks = []
        if not probs:
            return masks
        for p in probs:
            m = [x < self.config.prob_threshold for x in p]
            masks.append(m)

        return masks

    def prob2mask(self, prob):
        """
        >>> cr = BaseCorrecter(CorrecterConfig)
        >>> cr.prob2mask([0.99,0.85,1.00])
        '[0,1,0]'
        """
        if not prob:
            return []
        mask = [x < self.config.prob_threshold for x in prob]

        return mask

    @staticmethod
    def compile_regulars():
        alphabet = re.compile(r'[a-zA-ZＡ-Ｚａ-ｚ]')
        chinese = re.compile(r'[\u4E00-\u9FA5]')
        traditional_chinese = re.compile(r'[褔変絶値萬與醜專業叢東絲丟丟兩嚴並喪個爿豐臨為麗舉麼義烏樂喬習鄉書買亂乾亂爭於虧雲亙亙亞亞產畝親'
                                         r'褻嚲億僅僕從侖倉儀們價伕眾優夥會傴傘偉傳傷倀倫傖偽佇佇佈體佔佘餘傭僉併來侖俠侶僥偵側僑儈儕儂侶侷'
                                         r'俁係俠俁儔儼倆儷儉倀倆倉個們倖倣倫債傾偉傯側偵偸偺僂偽僨償傑傖傘備傚傢儻儐儲儺傭傯傳傴債傷傾僂僅'
                                         r'僉僑僕僞僥僨僱價儀儂億儅儈儉儐儔儕儘償優儲儷儸儹儺儻儼兒兇兌兌兒兗兗黨內兩蘭關興茲養獸囅內岡冊冊'
                                         r'寫軍農塚冪馮沖決況凍淨凃淒涼淩凍減湊凜凜凟幾鳳処鳧憑凱凱凴擊氹鑿芻劃劉則剛創刪別刪別剗剄劊劌剴劑'
                                         r'剄則剋剮劍剗剛剝剝劇剮剴創剷劃劄劇劉劊劌劍劑劒勸辦務勱動勵勁勞勢勁勳動勗務勩勛勝勞勢勣勦勩勱勳勵'
                                         r'勸勻勻匭匭匱匯匱匲匳匵區醫區華協協單賣蔔盧鹵臥衛卻卹巹卻廠廳曆厲壓厭厙廁厙厛厠廂厴厤廈廚廄厭廝厰'
                                         r'厲厴縣參參靉靆雙發變敘疊叢葉號歎嘰籲後吒嚇呂嗎唚噸聽啟吳吳呂嘸囈嘔嚦唄員咼嗆嗚詠哢嚨嚀噝吒諮噅鹹'
                                         r'咼響啞噠嘵嗶噦嘩噲嚌噥喲員哢唄唕唚嘜嗊嘮啢嗩唕喚唸問啓啗啞啟啢啣嘖嗇囀齧囉嘽嘯喒喚喦喪喫喬單喲噴'
                                         r'嘍嚳嗆嗇嗊嗎嗚嗩囁噯嗶嘆嘍嘔嘖嘗噓嘜嚶嘩嘮嘯嘰囑嘵嘸嘽噁噅噓嚕噝噠噥噦噯噲噴噸噹嚀嚇嚌嚐嚕嚙囂嚥'
                                         r'嚦嚨嚮謔嚲嚳嚴嚶嚻囀囁囂囅囈囉囌囑囘團囪囬園囯囪圍圇國圖圓圇國圍園圓圖團聖壙場壞塊堅壇壢壩塢墳墜'
                                         r'坰壟壟壚壘墾坰堊墊埡墶壋塏堖垵垻塒塤堝墊埡垵埰執堅堊塹墮堖堝堦堯報場堿壪塊塋塏塒塗塚塢塤塲塵塹塼'
                                         r'墊牆墜墝墮墰墳墶墻墾壇壋壎壓壘壙壚壜壞壟壠壢壩壪壯壯聲殼壺壼壺壼壽夀處備複夠夠夢夥頭誇夾奪夾奩奐'
                                         r'奮奐獎奧奧奩奪奮妝婦媽妝嫵嫗媯姍姍薑姦姪婁婭嬈嬌孌娛娬娛媧嫻婁婦婬婭嫿嬰嬋嬸媧媼媮媯媼媽嫋嬡嬪嫗'
                                         r'嬙嫵嫺嫻嫿嬀嬈嬋嬌嬙嬝嬡嬤嬪嬭嬰嬤嬸嬾孃孌孫學孿孫學孿寧寶實寵審憲宮宮寬賓寢寢實寧審寫寬寵寶對尋'
                                         r'導壽尅將將專尋對導爾塵嘗堯尲尷尷屍盡層屭屆屜屆屍屓屜屬屢屢層屨屨屬屭嶼歲豈嶇崗峴嶴嵐島岡嶺嶽崠巋'
                                         r'嶨嶧峽嶢嶠崢巒峴島峽嶗崍嶮崍崐崑崗崙崠崢崬嶄崳嵐嵗嶸嶔崳嶁嶁嶄嶇嶔嶗嶠嶢嶧嶨嶮嶴嶸嶺嶼嶽巔巋巒巔'
                                         r'巖鞏巰巰巹幣帥師幃帳簾幟帥帶幀師幫幬帳帶幘幗幀冪幃幗幘襆幟幣幫幬幱幹並幹幾廣莊慶廬廡庫應廟龐廢庫'
                                         r'廎廁廂廄廈廎廕廚廝廟廠廡廢廣廩廩廬廳廻廼開異棄弔張彌弳彎弳張強彈強彆彈彊彌彎歸當錄彙彜彞彠彠彥彥'
                                         r'彫徹彿徑後徑徠從徠禦復徬徴徵徹憶懺憂愾懷態慫憮慪悵愴憐總懟懌恆戀恥懇惡慟懨愷惻惱惲悅悅愨懸慳憫悵'
                                         r'悶悽驚惡懼慘懲憊愜慚憚慣惱惲惻湣愛愜慍憤憒愨愴愷愾願慄慇態慍懾慘慙慚慟慣慤慪慫憖慮慳慴慶慼慾憂憊'
                                         r'憐憑憒憖憚憤憫憮憲憶懇應懌懍懣懶懍懕懞懟懣懨懲懶懷懸懺懼懽懾戀戇戇戔戲戔戧戰戧戩戩戯戰戲戶戶紮撲'
                                         r'扡扡執擴捫掃揚擾撫拋摶摳掄搶護報擔拋擬攏揀擁攔擰撥擇掛摯攣掗撾撻挾撓擋撟掙擠揮撏挾撈損撿換搗捨捫'
                                         r'據捲撚掃掄掗掙掛採擄摑擲撣摻摜揀揚換揮摣揹攬撳攙擱摟攪搆搇損搖搗搶攜搾攝攄擺搖擯攤摑摜摟摣摯摳摶'
                                         r'摺摻攖撈撏撐撐撓撚撟撣撥撫撲撳攆擷擼攛撻撾撿擁擄擇擊擋擔擕據擻擠擡擣擧擬擯擰擱擲擴擷擺擻擼擾攄攆'
                                         r'攏攢攔攖攙攛攜攝攢攣攤攩攪攬攷敵敍敗敘斂敭數敵數敺斂斃齋斕斕鬥斬斬斷斷於旂無舊時曠暘昇曇晝曨顯時'
                                         r'晉晉曬曉曄暈暉晝暫暈暉暘暢曖暫暱曄曆曇曉曏曖曠曡曨曬書會朧劄術樸機殺雜權條來楊榪傑東極構樅樞棗櫪'
                                         r'梘棖槍楓梟枴櫃檸柵柺檉梔柵標棧櫛櫳棟櫨櫟欄樹棲樣欒棬椏橈楨榿橋樺檜槳樁桿梔梘條梟夢梱檮棶檢欞棄棖'
                                         r'棗棟棧棬棲棶槨椏櫝槧欏橢楊楓楨業極樓欖櫬櫚櫸榦榪榮榿槃構槍槓檟檻檳櫧槧槨槳槼樁樂樅樑樓標樞樣橫檣'
                                         r'櫻樷樸樹樺橈橋機橢櫫橫橰櫥櫓櫞檁檉簷檜檟檢檣檁檮檯檳檸檻檾櫂櫃櫓櫚櫛櫝櫞櫟櫥櫧櫨櫪櫫櫬櫳櫸櫺櫻欄'
                                         r'權欏欑欒欖欞歡歟歐欽歎歐歗歛歟歡歲歷歸殲歿歿殤殘殞殮殘殫殞殯殤殫殮殯殲毆殺殼毀毀轂毆毉畢斃氈毧毬'
                                         r'毿毿氂氌氈氊氌氣氫氣氬氫氬氳氳氹氾匯漢汎汙汚汙湯洶決沍沒遝沖溝沒灃漚瀝淪滄渢溈滬濔況濘淚澩瀧瀘濼'
                                         r'瀉潑澤涇潔灑洩洶窪浹淺漿澆湞溮濁測澮濟瀏滻渾滸濃潯濜浹塗涇湧涖濤澇淶漣潿渦溳渙滌潤澗漲澀涼澱淒淚'
                                         r'淥淨淩淪淵淶淺淵淥漬瀆漸澠漁瀋滲渙減渢渦溫測遊渾湊湞湣湧湯灣濕潰濺漵漊溈準溝溫溮溳溼滄滅滌滎潷滙'
                                         r'滾滯灩灄滿瀅濾濫灤濱灘澦滬滯滲滷滸滻滾滿漁漊漚漢漣濫漬漲漵漸漿潁瀠瀟瀲濰潑潔潙潛潛潟潤潯潰瀦潷潿'
                                         r'澀澁澂澆澇澗瀾澠澤澦澩澮澱濁濃瀨瀕濔濕濘濛濜濟濤濫濬濰濱濶濺濼濾瀅瀆瀉瀋瀏瀕瀘瀝瀟瀠瀦瀧瀨瀰瀲瀾'
                                         r'灃灄灝灑灕灘灝灣灤灧灩滅燈靈災災燦煬爐燉煒熗炤點為煉熾爍爛烴烏燭煙煩燒燁燴燙燼熱烴煥燜燾無煆煆煇'
                                         r'煉煒煖煙煢煥煩煬熒熗熱熲熾燁燄燈燉燐燒燙燜營燦燬燭燴燻燼燾燿爍爐爗爛爭愛爲爺爺爾爿牀牆牋牘牐牘犛'
                                         r'牴牽犧牽犢犖犛強犢犧狀獷獁猶狀狽麅獮獰獨狹獅獪猙獄猻狹狽獫獵獼猙玀豬貓蝟獻猶猻獁獃獄獅獎獨獪獫獺'
                                         r'獮獰獲獵獷獸獺獻獼玀玆璣璵瑒瑪玨瑋環現瑲璽瑉玨琺瓏珮璫琿現琍璡璉瑣琯琺瓊琿瑉瑋瑒瑣瑤瑩瑪瑯瑲瑤璦'
                                         r'璿璉瓔璡璣璦璫環璵璽璿瓊瓏瓚瓔瓚甕甌甌甎甕甖產産甦甯電畫暢畝畢畫異畱佘疇當疇疊癤療瘧癘瘍鬁瘡瘋皰'
                                         r'癰痙癢瘂痙痠癆瘓癇癡痺瘂癉瘮瘉瘋瘍瘓瘞瘺瘞瘡瘧癟癱瘮瘺瘻癮癭療癆癇癉癒癘癩癟癡癢癬癤癥癧癩癲癬癭'
                                         r'癮臒癰癱癲發皚皚皰皺皸皸皺盃盞鹽監蓋盜盤盜盞盡監盤盧盪瞘眎眡眥眥矓眾著睜睏睞瞼睜睞瞞瞘瞞矚瞼矇矓'
                                         r'矚矯矯磯矽礬礦碭碼磚硨硯碸砲礪礱礫礎硜硃矽碩硤磽磑礄硜硤硨確硯硶鹼礙磧磣碩碭堿碸镟確碼磐磑滾磚磣'
                                         r'磧磯磽礄礎礙礦礪礫礬礮礱禮禕祐祕禰禎禱禍祿稟祿禪禍禎禕禦禪禮禰禱離禿禿稈秈種積稱穢穠稅穭稈稅稜稟'
                                         r'穌稭種稱穩穀穌積穎穡穠穡穢穨穩穫穭窮竊竅窯竄窩窺竇窩窪窶窮窯窰窶窺竄竅竇竈竊豎竝競竪競篤筍筆筧箋'
                                         r'籠籩筆筍築篳篩簹箏筧籌簽簡箇箋箏籙箠簀篋籜籮簞簫節範築篋簣簍篛篠篤篩籃籬篳簀簍簑籪簞簡簣簫簷簹簽'
                                         r'簾籟籃籌籐籙籜籟籠籢籤籥籩籪籬籮籲糴類秈糶糲粵粧糞粬糧粵糝餱糝糞糢糧糰糲糴糶糸糾紀紂約紅紆紇紈紉'
                                         r'紋納紐紓純紕紖紗紘紙級紛紜紝紡紥緊紮細紱紲紳紵紹紺紼紿絀終絃組絆絍絎絏結絕絛絝絞絡絢給絨絰統絲絳'
                                         r'縶絹綁綃綆綈綉綌綏綑經綜綞綠綢綣綫綬維綯綰綱網綳綴綵綸綹綺綻綽綾綿緄緇緊緋緍緒緓緔緗緘緙線緜緝緞'
                                         r'締緡緣緤緦編緩緬緯緱緲練緶緹緻緼縂縈縉縊縋縐縑縕縗縚縛縝縞縟縣縧縫縭縮縯縱縲縴縵縶縷縹總績繃繅繆'
                                         r'繈繒織繕繖繙繚繞繡繢繦繩繪繫繭繮繯繰繳繹繼繽繾纇纈纊續纍纏纓纖纘纜糸糾紆紅紂纖紇約級紈纊紀紉緯紜'
                                         r'紘純紕紗綱納紝縱綸紛紙紋紡紵紖紐紓線紺絏紱練組紳細織終縐絆紼絀紹繹經紿綁絨結絝繞絰絎繪給絢絳絡絕'
                                         r'絞統綆綃絹繡綌綏絛繼綈績緒綾緓續綺緋綽緔緄繩維綿綬繃綢綯綹綣綜綻綰綠綴緇緙緗緘緬纜緹緲緝縕繢緦綞'
                                         r'緞緶線緱縋緩締縷編緡緣縉縛縟縝縫縗縞纏縭縊縑繽縹縵縲纓縮繆繅纈繚繕繒韁繾繰繯繳纘缽罌罈罋罌罎罏網'
                                         r'羅罰罷罰羆罵罷罸羈羅羆羈羋羥羨羢羥羨義羶習翹翽翬翬翹翺翽耑耡耮耬耬耮聳恥聶聾職聹聯聖聞聵聰聯聰聲'
                                         r'聳聵聶職聹聼聽聾肅肅腸膚膁腎腫脹脅膽勝朧腖臚脛膠脅脇脈脈膾髒臍腦膿臠腳脛脣脩脫脫腡臉脹臘醃腎腖膕'
                                         r'腡腦腫齶腳腸膩靦膃騰膁膃臏膕膚膠膩膽膾膿臉臍臏臒臘臚臢臟臠臢臥臨臯臺輿與興舉舊舖舘艤艦艙艫艙艢艣'
                                         r'艤艦艪艫艱艱豔艷艸艸藝節羋薌蕪蘆芻蓯葦藶莧萇蒼苧蘇檾苧蘋範莖蘢蔦塋煢繭茲荊荊薦薘莢蕘蓽蕎薈薺蕩榮'
                                         r'葷滎犖熒蕁藎蓀蔭蕒葒葤藥蒞莊莖蓧莢莧萊蓮蒔萵薟獲蕕瑩鶯蓴華菴菸萇萊蘀蘿螢營縈蕭薩萬萵葉葒著葠葤葦'
                                         r'葯蔥葷蕆蕢蔣蔞蒐蒓蒔蒞蒼蓀蓆蓋藍薊蘺蓡蕷鎣驀蓧蓮蓯蓴蓽蔆蔔蔞蔣蔥蔦蔭蔴薔蘞藺藹蕁蕆蕎蕒蕓蕕蕘蕢蕩'
                                         r'蕪蕭蘄蘊蕷薈薊薌薑薔薘薟薦薩藪薰薺藍藎蘚藝藥藪藶藹藺蘀蘄蘆蘇蘊蘋蘚蘞蘢蘭蘺蘿虜慮處虛虛虜號虧蟲虯'
                                         r'蟣虯雖蝦蠆蝕蟻螞蠶蠔蜆蠱蠣蟶蠻蟄蛺蟯螄蠐蛺蛻蜆蛻蝸蠟蠅蟈蟬蠍蝕蝟蝦蝨蝸螻蠑螿螄螘螞螢蟎螻螿蟄蟈蟎'
                                         r'蠨蟣蟬蟯蟲蟶蟻蠅蠆蠍蠐蠑蠔蠟蠣蠨蠱蠶蠻釁衆衊術銜衚衛衝衞補襯袞衹襖嫋褘襪袞襲襏裝襠褌裊裌裏補裝裡'
                                         r'褳襝褲襇製複褌褘褸褲褳襤褸褻繈襆襇襍襏襴襖襝襠襤襪襯襲襴覈見覎規覓覔視覘覜覡覥覦親覬覯覰覲覷覺覻'
                                         r'覽覿觀見觀覎規覓視覘覽覺覬覡覿覥覦覯覲覷觝觴觸觶觴觶觸訁訂訃計訊訌討訏訐訒訓訕訖託記訛訝訟訢訣訥'
                                         r'訦訩訪設許訴訶診註証詁詆詎詐詒詔評詖詗詘詛詞讋詠詡詢詣試詩詫詬詭詮詰話該詳詵詼詾詿誄誅誆誇譽謄誌'
                                         r'認誑誒誕誘誚語誠誡誣誤誥誦誨說説誰課誶誹誼調諂諄談諉請諍諏諑諒論諗諛諜諝諞諡諢諤諦諧諫諭諮諱諳諶'
                                         r'諷諸諺諼諾謀謁謂謄謅謊謎謐謔謖謗謙謚講謝謠謨謫謬謳謹謾譁譆證譌譎譏譖識譙譚譜譟譫譭譯議譴護譸譽譾'
                                         r'讀讁讅變讋讌讎讐讒讓讕讖讚讛讜讞訁計訂訃認譏訐訌討讓訕訖訓議訊記訒講諱謳詎訝訥許訛論訩訟諷設訪訣'
                                         r'證詁訶評詛識詗詐訴診詆謅詞詘詔詖譯詒誆誄試詿詩詰詼誠誅詵話誕詬詮詭詢詣諍該詳詫諢詡譸誡誣語誚誤誥'
                                         r'誘誨誑說誦誒請諸諏諾讀諑誹課諉諛誰諗調諂諒諄誶談誼謀諶諜謊諫諧謔謁謂諤諭諼讒諮諳諺諦謎諞諝謨讜謖'
                                         r'謝謠謗諡謙謐謹謾謫譾謬譚譖譙讕譜譎讞譴譫讖穀谿豈豎豐豔豬豶豶貍貓貝貞貟負財貢貧貨販貪貫責貯貰貲貳'
                                         r'貴貶買貸貺費貼貽貿賀賁賂賃賄賅資賈賉賊賍賑賒賓賔賕賙賚賛賜賞賠賡賢賣賤賦賧質賫賬賭賮賴賵賸賺賻購'
                                         r'賽賾贄贅贇贈贊贋贍贏贐贓贔贖贗贛贜貝貞負貟貢財責賢敗賬貨質販貪貧貶購貯貫貳賤賁貰貼貴貺貸貿費賀貽'
                                         r'賊贄賈賄貲賃賂贓資賅贐賕賑賚賒賦賭齎贖賞賜贔賙賡賠賧賴賵贅賻賺賽賾贗贊贇贈贍贏贛赬赬趙趕趨趕趙趨'
                                         r'趲趲躉躍蹌蹠躒跡踐躂蹺蹕躚躋跼踴躊踐踡蹤躓躑踴蹌躡蹣蹕蹟蹠蹣蹤躕蹺躥躂躉躊躋躍躪躑躒躓躕躚躦躡躥'
                                         r'躦躪軀躰軀軃車軋軌軍軑軒軔軛軟軤軫軲軸軹軺軻軼軾較輅輇輈載輊輒輓輔輕輛輜輝輞輟輥輦輩輪輬輭輯輳輸'
                                         r'輻輼輾輿轀轂轄轅轆轉轍轎轔轟轡轢轤車軋軌軒軑軔轉軛輪軟轟軲軻轤軸軹軼軤軫轢軺輕軾載輊轎輈輇輅較輒'
                                         r'輔輛輦輩輝輥輞輬輟輜輳輻輯轀輸轡轅轄輾轆轍轔辭辤辦辯辮辭辮辯農辳邊遼達遷迆過邁運還這進遠違連遲邇'
                                         r'逕迴跡迺適選遜遞逕這連邐週進邏遊運過達違遺遙遜遝遞遠遙適遲遷選遺遼邁還邇邊邏邐鄧鄺鄔郵鄒鄴鄰鬱郃'
                                         r'郤郟鄶鄭鄆郟郤酈鄖郵鄲鄆鄉鄒鄔鄕鄖鄘鄧鄭鄰鄲鄴鄶鄺酈醞醱酧醯醬釅釃釀醃醖醜醞醫醬醯醱醻醼釀釁釃釅'
                                         r'釋釋裡釐釓釔釕釗釘釙針釣釤釦釧釩釬釵釷釹釺鈀鈁鈃鈄鈅鈈鈉鈍鈎鈐鈑鈒鈔鈕鈞鈡鈣鈥鈦鈧鈮鈰鈳鈴鈷鈸鈹'
                                         r'鈺鈽鈾鈿鉀鉄钜鉆鉈鉉鉋鉍鉑鉕鉗鉚鉛鉞鉢鉤鉦鉬鉭鉲鑒鉶鉸鉺鉻鉿銀銃銅銍銑銓銕銖銘銚銛銜銠銣銥銦銨銩'
                                         r'銪銫銬鑾銱銲銳銷銹銻銼鋁鋂鋃鋅鋇鋌鋏鋒鋙鋜鋝鋟鋣鋤鋥鋦鋨鋩鋪鋮鋯鋰鋱鋶鋸鋻鋼錁錄錆錇錈錏錐錒錕錘'
                                         r'錙錚錛錟錠錡錢錦錨錩錫錮錯錳錶錸錼鏨鍀鍁鍃鍆鍇鍈鍊鍋鍍鍔鍘鍚鍛鍠鍤鍥鍩鍫鍬鍰鍵鍶鍺鍼鍾鎂鎄鎇鎊鎋'
                                         r'鎔鎖鎘鎚鎛鎡鎢鎣鎦鎧鎩鎪鎬鎮鎰鎲鎳鎵鎸鎿鏃鏇鏈鏌鏍鏐鏑鏗鏘鏚鏜鏝鏞鏟鏡鏢鏤鏨鏰鏵鏷鏹鏽鐃鐋鐐鐒鐓'
                                         r'鐔鐘鐙鐝鐠鐦鐧鐨鐫鐮鐲鐳鐵鐶鐸鐺鐿鑄鑊鑌鑑鑒鑔鑕鑛鑞鑠鑣鑤鑥鑪鑭鑰鑱鑲鑷鑹鑼鑽鑾鑿钁钂釓釔針釘釗'
                                         r'釙釕釷釺釧釤鈒釩釣鍆釹鍚釵鈃鈣鈈鈦钜鈍鈔鐘鈉鋇鋼鈑鈐鑰欽鈞鎢鉤鈧鈁鈥鈄鈕鈀鈺錢鉦鉗鈷缽鈳鉕鈽鈸鉞'
                                         r'鑽鉬鉭鉀鈿鈾鐵鉑鈴鑠鉛鉚鈰鉉鉈鉍鈮鈹鐸鉶銬銠鉺鋩錏銪鋮鋏鋣鐃銍鐺銅鋁銱銦鎧鍘銖銑鋌銩銛鏵銓鎩鉿銚'
                                         r'鉻銘錚銫鉸銥鏟銃鐋銨銀銣鑄鐒鋪鋙錸鋱鏈鏗銷鎖鋰鋥鋤鍋鋯鋨鏽銼鋝鋒鋅鋶鉲鐧銳銻鋃鋟鋦錒錆鍺鍩錯錨錛'
                                         r'錡鍀錁錕錩錫錮鑼錘錐錦鑕鍁錈鍃錇錟錠鍵鋸錳錙鍥鍈鍇鏘鍶鍔鍤鍬鍾鍛鎪鍠鍰鎄鍍鎂鏤鎡鐨鋂鏌鎮鎛鎘鑷钂'
                                         r'鐫鎳錼鎦鎬鎊鎰鎵鑌鎔鏢鏜鏝鏍鏰鏞鏡鏑鏃鏇鏐鐔钁鐐鏷鑥鐓鑭鐠鑹鏹鐙鑊鐳鐶鐲鐮鐿鑔鑣鑞鑱鑲長長門閂閃'
                                         r'閆閈閉開閌閎閏閑閒間閔閘閙閡関閣閤閥閨閩閫閬閭閱閲閶閹閻閼閽閾閿闃闆闈闊闋闌闍闐闒闓闔闕闖闚關闞'
                                         r'闠闡闢闤闥門閂閃閆閈閉問闖閏闈閑閎間閔閌悶閘鬧閨聞闥閩閭闓閥閣閡閫鬮閱閬闍閾閹閶鬩閿閽閻閼闡闌闃'
                                         r'闠闊闋闔闐闒闕闞闤隊阬阯陽陰陣階際陸隴陳陘陝陘陝陞陣隉隕險陰陳陸陽隂隄隉隊階隨隱隕隖際隣隨險隱隴'
                                         r'隸隷隸隻雋難雋雛雖雙雛雜雞讎離難雲靂電霧霽黴霑霛霤霧靄霽靂靄靆靈靉靚靜靚靜靣靨靦靨靭鞀鞉鞏韃鞽鞦'
                                         r'韉韝鞽韁韃韆韉韋韌韍韓韙韜韝韞韤韋韌韍韓韙韞韜韻韻響頁頂頃項順頇須頊頌頎頏預頑頒頓頗領頜頡頤頦頫'
                                         r'頭頮頰頲頴頷頸頹頻頽顆題額顎顏顒顓顔願顙顛類顢顥顧顫顬顯顰顱顳顴頁頂頃頇項順須頊頑顧頓頎頒頌頏預'
                                         r'顱領頗頸頡頰頲頜潁熲頦頤頻頮頹頷頴穎顆題顒顎顓顏額顳顢顛顙顥纇顫顬顰顴風颭颮颯颱颳颶颸颺颻颼飀飃'
                                         r'飄飆飇飈風颺颭颮颯颶颸颼颻飀飄飆飆飛飛飢飣飥饗飩飪飫飭飯飲飴飼飽飾飿餃餄餅餉養餌饜餎餏餑餒餓餕餖'
                                         r'餘餚餛餜餞餡館餱餳餵餶餷餺餼餽餾餿饁饃饅饈饉饊饋饌饑饒饗饜饝饞饢飣饑飥餳飩餼飪飫飭飯飲餞飾飽飼飿'
                                         r'飴餌饒餉餄餎餃餏餅餑餖餓餘餒餕餜餛餡館餷饋餶餿饞饁饃餺餾饈饉饅饊饌饢馬馭馮馱馳馴馹駁駐駑駒駔駕駘'
                                         r'駙駛駝駟駡駢駭駮駰駱駸駿騁騂騅騌騍騎騏騐騖騗騙騣騤騫騭騮騰騶騷騸騾驀驁驂驃驄驅驊驌驍驏驕驗驘驚驛'
                                         r'驟驢驤驥驦驪驫馬馭馱馴馳驅馹駁驢駔駛駟駙駒騶駐駝駑駕驛駘驍罵駰驕驊駱駭駢驫驪騁驗騂駸駿騏騎騍騅騌'
                                         r'驌驂騙騭騤騷騖驁騮騫騸驃騾驄驏驟驥驦驤骾髏髖髕髏髒體髕髖髩髮鬁鬆鬍鬢鬚鬢鬥鬦鬧鬨鬩鬭鬮鬱魘魎魎魘'
                                         r'魚魛魢魨魯魴魷魺鮁鮃鮊鮋鮌鮍鮎鮐鮑鮒鮓鮚鮜鮞鮦鮪鮫鮭鮮鮳鮶鮷鮺鯀鯁鯇鯉鯊鯒鯔鯕鯖鯗鯛鯝鯡鯢鯤鯧鯨'
                                         r'鯪鯫鯰鯴鯵鯷鯽鯿鰁鰂鰃鰈鰉鰌鰍鰏鰐鰒鰓鰛鰜鰟鰠鰣鰥鰨鰩鰭鰮鰱鰲鰳鰵鰷鰹鰺鰻鰼鰾鱂鱅鱈鱉鱒鱓鱔鱖鱗'
                                         r'鱘鱝鱟鱠鱣鱤鱧鱨鱭鱯鱷鱸鱺魚魛魢魷魨魯魴魺鮁鮃鯰鱸鮋鮓鮒鮊鮑鱟鮍鮐鮭鮚鮳鮪鮞鮦鰂鮜鱠鱭鮫鮮鮺鯗鱘'
                                         r'鯁鱺鰱鰹鯉鰣鰷鯀鯊鯇鮶鯽鯒鯖鯪鯕鯫鯡鯤鯧鯝鯢鯰鯛鯨鯵鯴鯔鱝鰈鰏鱨鯷鰮鰃鰓鱷鰍鰒鰉鰁鱂鯿鰠鼇鰭鰨鰥'
                                         r'鰩鰟鰜鰳鰾鱈鱉鰻鰵鱅鰼鱖鱔鱗鱒鱯鱤鱧鱣鳥鳧鳩鳲鳳鳴鳶鴆鴇鴉鴒鴕鴛鴝鴞鴟鴣鴦鴨鴬鴯鴰鴴鴻鴿鵂鵃鵐鵑'
                                         r'鵒鵓鵜鵝鵞鵠鵡鵪鵬鵮鵯鵲鵶鵷鵾鶇鶉鶊鶓鶖鶘鶚鶡鶤鶥鶩鶬鶯鶲鶴鶹鶺鶻鶼鶿鷀鷁鷂鷄鷊鷓鷖鷗鷙鷚鷥鷦鷫'
                                         r'鷯鷰鷲鷳鷴鷸鷹鷺鷼鸇鸌鸎鸏鸕鸘鸚鸛鸝鸞鳥鳩雞鳶鳴鳲鷗鴉鶬鴇鴆鴣鶇鸕鴨鴞鴦鴒鴟鴝鴛鴬鴕鷥鷙鴯鴰鵂鴴'
                                         r'鵃鴿鸞鴻鵐鵓鸝鵑鵠鵝鵒鷳鵜鵡鵲鶓鵪鶤鵯鵬鵮鶉鶊鵷鷫鶘鶡鶚鶻鶖鶿鶥鶩鷊鷂鶲鶹鶺鷁鶼鶴鷖鸚鷓鷚鷯鷦鷲'
                                         r'鷸鷺鸇鷹鸌鸏鸛鸘鹵鹹鹺鹼鹽鹺麅麗麥麥麩麪麯麴麵麩麼麽黃黃黌黌點黶黨黷黲黲黴黶黷黽黽黿鼂鼇鼈鼉黿鼂'
                                         r'鼉鼕鞀鼴鼴齇齇齊齋齎齏齊齏齒齔齕齗齙齜齟齠齡齣齦齧齪齬齲齶齷齒齔齕齗齟齡齙齠齜齦齬齪齲齷龍龐龔龕'
                                         r'龍龔龕龜龜]')
        number = re.compile(r'[0-9]')

        regulars = {'alphabet':alphabet, 'chinese':chinese, 'traditional':traditional_chinese, 'number':number}

        return regulars
