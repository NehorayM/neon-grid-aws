#!/usr/bin/env python3
"""Rewrite the AWS glossary in Hebrew, and make everything that shows it read RTL.

The old definitions were terse English labels — "Stateful instance-level firewall.
Allow rules only." That tells you nothing you did not already know from the name.
Each entry is rewritten to say what the service actually is, and then the one fact
that decides exam questions about it.

The keys stay in English: `conceptsFor()` matches them against the question text,
so translating a key would break the matching. Only the definitions change.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"

HEB = {
"ec2": "שרת וירטואלי שאתה שוכר לפי שנייה. אתה אחראי על מערכת ההפעלה, העדכונים והגיבוי — AWS רק על החומרה שמתחת.",
"lambda": "מריץ קוד בלי שום שרת. משלמים על אלפיות השנייה שרצו בפועל, ויש תקרה קשיחה של 15 דקות להרצה אחת.",
"fargate": "מריץ קונטיינרים בלי לנהל שרתים. אתה אומר כמה מעבד וזיכרון צריך, AWS מוצא איפה להריץ.",
"ecs": "מנהל הקונטיינרים של AWS. יכול לרוץ על שרתי EC2 שלך או על Fargate בלי שרתים בכלל.",
"eks": "Kubernetes מנוהל. בוחרים בו כשחייבים דווקא את ה-API של Kubernetes; אחרת ECS פשוט יותר וזול יותר.",
"ecr": "מחסן פרטי לאימג׳ים של Docker, עם הרשאות IAM וחיבור ישיר ל-ECS ול-EKS.",
"s3": "אחסון אובייקטים: מעלים קובץ ומקבלים כתובת. עמידות של אחת עשרה תשיעיות ובלי תקרת נפח — אבל זה לא דיסק ולא מערכת קבצים.",
"glacier": "מחלקת הארכיון של S3. הזולה ביותר, אבל שליפה לוקחת דקות עד שעות — לא למשהו שצריך עכשיו.",
"ebs": "דיסק וירטואלי שמתחבר לשרת EC2 אחד בלבד וחי באזור זמינות אחד. כדי להעביר אותו למקום אחר עושים snapshot.",
"efs": "מערכת קבצים משותפת ל-Linux שהרבה שרתים מחוברים אליה בו-זמנית. גדלה לבד ופרוסה על כמה אזורי זמינות.",
"fsx": "מערכות קבצים מוכרות כשירות מנוהל: FSx for Windows לשיתופי SMB ו-Active Directory, ו-Lustre לחישוב כבד מול נתונים ב-S3.",
"rds": "בסיס נתונים רלציוני מנוהל — MySQL,‏ PostgreSQL ואחרים. Multi-AZ נותן זמינות, read replica נותן ביצועי קריאה. שני דברים שונים.",
"aurora": "בסיס הנתונים של AWS, תואם MySQL ו-PostgreSQL. שומר שישה עותקים בשלושה אזורי זמינות, והאחסון גדל לבד עד 128 טרה.",
"dynamodb": "בסיס נתונים NoSQL בלי שרתים, עם זמן תגובה של אלפיות שנייה בכל עומס. פריט בודד מוגבל ל-400 קילובייט — מעבר לזה שומרים ב-S3.",
"elasticache": "זיכרון מטמון מנוהל, Redis או Memcached, שמוריד עומס מבסיס הנתונים. רק Redis שורד נפילה של שרת.",
"redshift": "מחסן נתונים לשאילתות אנליטיות כבדות על טרות של מידע. לא מיועד לעבודה השוטפת של אפליקציה.",
"athena": "שאילתות SQL ישירות על קבצים שיושבים ב-S3, בלי להקים שום שרת. משלמים לפי כמות המידע שנסרקה.",
"glue": "שירות ETL בלי שרתים, ובנוסף קטלוג מרכזי שיודע מה המבנה של כל טבלה וקובץ.",
"emr": "אשכולות Hadoop ו-Spark מנוהלים, לעיבוד כמויות מידע גדולות בקוד שלך.",
"kinesis": "זרם נתונים בזמן אמת. Data Streams כשצריך שליטה, כמה צרכנים או הרצה חוזרת; Firehose כשרק רוצים לשפוך לתוך S3 בלי לכתוב קוד.",
"sqs": "תור הודעות. הצרכן מושך הודעה, מעבד אותה ומוחק — וכך שני צדדים עובדים בקצב שלהם ולא נופלים ביחד.",
"sns": "הודעות בשיטת פרסום-מנוי: הודעה אחת נשלחת בו-זמנית לכל מי שנרשם אליה, וכל מנוי יכול לסנן מה מעניין אותו.",
"eventbridge": "אפיק אירועים שמנתב אירועים מ-AWS, משירותי SaaS או מהקוד שלך לפי כללים. הדרך הנקייה לנתק בין מערכות.",
"step functions": "מנצח על תהליך מרובה שלבים: מי רץ אחרי מי, מה קורה בכישלון, ואיפה ממתינים לאישור אנושי.",
"amazon mq": "ActiveMQ או RabbitMQ מנוהלים, לאפליקציות קיימות שכבר מדברות בפרוטוקולים כמו AMQP או MQTT.",
"api gateway": "שער כניסה מנוהל ל-API: אימות, הגבלת קצב, מטמון ותיעוד — בלי שרת משלך מאחור.",
"cloudfront": "רשת הפצת תוכן גלובלית. שומרת עותק קרוב למשתמש, ויודעת לנעול דלי S3 כך שרק היא רשאית לקרוא ממנו.",
"global accelerator": "שתי כתובות IP קבועות שמנתבות כל משתמש לנקודה הבריאה הקרובה אליו, דרך הרשת הפנימית של AWS ולא דרך האינטרנט.",
"route 53": "שירות ה-DNS של AWS, עם בדיקות תקינות ושבע מדיניות ניתוב — לפי זמן תגובה, מיקום גיאוגרפי, משקל או גיבוי.",
"elb": "מאזן עומסים מנוהל. ALB לתעבורת HTTP, NLB ל-TCP מהיר במיוחד, ו-GWLB כדי להעביר תעבורה דרך רכיבי אבטחה.",
"alb": "מאזן עומסים בשכבה 7. מנתב לפי נתיב, דומיין או כותרת, ויודע לשלוח גם לקונטיינרים וגם ל-Lambda.",
"nlb": "מאזן עומסים בשכבה 4. השהיה זעירה, מיליוני בקשות בשנייה, וכתובת IP קבועה בכל אזור זמינות — מה שחומת אש של לקוח יכולה לאשר.",
"auto scaling": "מוסיף ומוריד שרתים לפי הביקוש בפועל, ומחליף אוטומטית שרת שנפל בבדיקת התקינות.",
"vpc": "הרשת הפרטית שלך בענן: רשתות משנה, טבלאות ניתוב ושערים. שום דבר לא נכנס ולא יוצא בלי שהגדרת.",
"nat gateway": "מאפשר לשרתים ברשת פרטית לצאת לאינטרנט, בלי לאפשר לאינטרנט להיכנס אליהם. חי באזור זמינות אחד — לעמידות צריך אחד בכל אזור.",
"internet gateway": "השער שמחבר VPC לאינטרנט. בלעדיו רשת משנה ציבורית היא לא באמת ציבורית.",
"security group": "חומת אש ברמת השרת. יש בה כללי התרה בלבד, והיא זוכרת חיבור — תשובה חוזרת עוברת אוטומטית.",
"nacl": "חומת אש ברמת רשת המשנה. אפשר לחסום במפורש, אבל היא לא זוכרת חיבור — צריך לפתוח גם את כיוון החזרה.",
"vpc endpoint": "גישה פרטית לשירות AWS בלי לצאת לאינטרנט. Gateway endpoint חינמי אבל רק ל-S3 ו-DynamoDB; interface endpoint עולה כסף ועובד כמעט לכל השאר.",
"privatelink": "חושף שירות מ-VPC אחד לתוך VPC אחר דרך כרטיס רשת פרטי, בלי לחבר את הרשתות ובלי חפיפת כתובות.",
"transit gateway": "נתב מרכזי שמחבר עשרות רשתות VPC ורשתות מקומיות, במקום עשרות חיבורים אחד-לאחד.",
"direct connect": "סיב פיזי ייעודי מהמשרד אל AWS. השהיה יציבה ורוחב פס גבוה — אבל הוא לא מוצפן מעצמו.",
"site-to-site vpn": "מנהרה מוצפנת דרך האינטרנט בין הרשת בארגון ל-VPC. מהיר להקים, אבל תלוי באיכות האינטרנט.",
"iam": "מי אתה ומה מותר לך: משתמשים, קבוצות, תפקידים ומדיניות. תמיד ההרשאה המינימלית שמספיקה לעבודה.",
"iam role": "הרשאות זמניות שגורם כלשהו לובש לרגע. זו התשובה הנכונה לשרת שצריך גישה, ולגישה בין חשבונות — אף פעם לא מפתח גישה קבוע.",
"sts": "השירות שמנפיק את ההרשאות הזמניות. הפעולה AssumeRole היא הבסיס לכל גישה בין חשבונות.",
"organizations": "ניהול הרבה חשבונות AWS יחד: חשבונית אחת, הנחות כמות, ומדיניות שחלה על כל החשבונות.",
"scp": "תקרת הרשאות לחשבונות בארגון. היא אף פעם לא נותנת הרשאה, רק מגבילה — וזה חל גם על משתמש ה-root.",
"identity center": "כניסה אחת לכל חשבונות AWS בארגון, מול ספק הזהויות הקיים שלכם. שמו הקודם היה AWS SSO.",
"cognito": "הרשמה והתחברות של משתמשי האפליקציה: user pool מטפל באימות, identity pool מחלק הרשאות AWS זמניות.",
"kms": "ניהול מפתחות ההצפנה. אתה קובע מי רשאי להשתמש בכל מפתח, וכל שימוש נרשם ב-CloudTrail — זה מה שמבדיל אותו מהצפנה רגילה.",
"cloudhsm": "רכיב חומרה ייעודי שרק אתה נכנס אליו. שליטה מלאה במפתחות — ואם איבדת מפתח, גם AWS לא יכולה לשחזר אותו.",
"secrets manager": "שומר סיסמאות ומפתחות ומחליף אותם אוטומטית בלוח זמנים שהגדרת, כולל חיבור מובנה ל-RDS.",
"parameter store": "אחסון הגדרות וסודות בתוך Systems Manager. זול יותר מ-Secrets Manager, אבל בלי החלפה אוטומטית.",
"acm": "תעודות TLS ציבוריות בחינם שמתחדשות לבד, ל-ELB,‏ CloudFront ו-API Gateway. אי אפשר לייצא אותן החוצה.",
"waf": "חומת אש לאפליקציה: חוסמת SQL injection ו-XSS ומגבילה קצב בקשות. מתחברת ל-ALB,‏ CloudFront או API Gateway — אף פעם לא ל-NLB.",
"shield": "הגנה מהתקפות מניעת שירות. Standard חינם ופועל תמיד; Advanced מוסיף צוות תגובה זמין והחזר על עלויות שההתקפה גרמה.",
"guardduty": "מזהה פעילות חשודה מתוך יומני CloudTrail, תעבורת הרשת ושאילתות DNS — בלי שתתקין שום דבר על השרתים.",
"inspector": "סורק אוטומטית פרצות אבטחה ידועות בשרתי EC2, באימג׳ים של קונטיינרים ובפונקציות Lambda.",
"macie": "מאתר מידע רגיש — מספרי זהות, כרטיסי אשראי, פרטים אישיים — שיושב בטעות בדליי S3.",
"cloudwatch": "מדדים, יומנים, התראות ולוחות מחוונים. שימו לב: זיכרון ומקום בדיסק אינם נמדדים מעצמם, צריך להתקין את הסוכן.",
"cloudtrail": "מתעד כל קריאת API בחשבון. זו התשובה לשאלה ״מי מחק את זה, ומתי״.",
"config": "עוקב אחרי ההגדרות של כל משאב לאורך זמן, ומתריע כשהגדרה חורגת מהכלל שקבעת — למשל דיסק בלי הצפנה.",
"x-ray": "עוקב אחרי בקשה בודדת בדרכה בין כל השירותים, כדי לגלות איפה בדיוק היא נתקעת.",
"cloudformation": "תיאור התשתית כקוד. כותבים קובץ אחד, ו-AWS בונה, מעדכן או מוחק לפיו את כל המשאבים יחד.",
"systems manager": "ניהול צי השרתים: חיבור בלי SSH ובלי פורט פתוח, עדכוני אבטחה, הרצת פקודות ומלאי תוכנה.",
"snowball": "ארגז פיזי שמגיע אליך בדואר. ממלאים אותו בטרות של מידע ושולחים חזרה — כשהרשת פשוט לא תספיק בזמן.",
"storage gateway": "גשר שמאפשר למערכות בארגון להמשיך לעבוד מול שיתוף קבצים או כונן כרגיל, כשבפועל המידע כבר יושב ב-AWS.",
"datasync": "מעביר כמויות גדולות של קבצים מהארגון אל S3,‏ EFS או FSx — בלוח זמנים, עם אימות שהכול הגיע שלם.",
"dms": "מעביר בסיסי נתונים אל AWS עם מינימום השבתה, גם כשמנוע המקור ומנוע היעד שונים.",
"sagemaker": "בונים, מאמנים ומפעילים מודלים של למידת מכונה מקצה לקצה, בלי לנהל שרתי אימון.",
"rekognition": "ניתוח תמונות ווידאו מוכן לשימוש: זיהוי עצמים, פנים ותוכן בעייתי, בלי לאמן מודל.",
"comprehend": "ניתוח טקסט חופשי: סנטימנט, ישויות וביטויי מפתח, בקריאת API אחת.",
"transcribe": "ממיר דיבור מוקלט לטקסט כתוב.",
"polly": "ממיר טקסט לדיבור שנשמע טבעי.",
"translate": "תרגום אוטומטי בין שפות.",
"textract": "מוציא טקסט, שדות וטבלאות ממסמכים סרוקים. לא רק OCR — הוא מבין גם את המבנה של הטופס.",
"well-architected": "שש עדשות לבחון בהן כל ארכיטקטורה: מצוינות תפעולית, אבטחה, אמינות, ביצועים, עלות וקיימות.",
"cost explorer": "רואים ומנתחים את ההוצאה בפועל לפי שירות, תגית או חשבון, ומקבלים תחזית קדימה.",
"budgets": "מגדירים תקציב ומקבלים התראה כשההוצאה — או התחזית שלה — עוברת את הסף.",
"savings plans": "מתחייבים להוצאה שעתית קבועה לשנה או לשלוש ומקבלים הנחה עמוקה, בלי לנעול סוג מכונה מסוים.",
"spot": "קיבולת פנויה בהנחה של עד 90%, אבל AWS יכולה לקחת אותה בחזרה בהתראה של שתי דקות. לא למשהו עם מצב שאסור לאבד.",
"reserved instance": "התחייבות לשנה או לשלוש למשפחת מכונות מסוימת, תמורת ההנחה הגדולה ביותר על עומס יציב.",
"placement group": "קובע איפה פיזית יישבו השרתים: cluster לקרבה מרבית ומהירות, spread להפרדה מלאה, partition לאשכולות גדולים.",
"multi-az": "עותק בכוננות באזור זמינות אחר שמחליף את הראשי אוטומטית כשהוא נופל. זמינות — לא ביצועים, ואי אפשר לקרוא ממנו.",
"read replica": "עותק לקריאה בלבד שמתעדכן ברקע ומוריד עומס קריאה מהראשי. אפשר לקדם אותו לראשי בשעת חירום.",
"rto": "כמה זמן מותר למערכת להיות מושבתת. RTO של חמש דקות דורש ארכיטקטורה אחרת לגמרי מ-RTO של יום.",
"rpo": "כמה מידע מותר לאבד. RPO של דקה אומר גיבוי כמעט רציף; RPO של יום מסתפק בגיבוי לילי.",
"pilot light": "אסטרטגיית התאוששות: הליבה — בדרך כלל בסיס הנתונים — רצה תמיד באזור השני, וכל השאר עולה רק כשקורה אסון.",
"warm standby": "אסטרטגיית התאוששות: עותק מוקטן אבל עובד במלואו רץ תמיד, ובאסון פשוט מגדילים אותו.",
}

s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ---------------------------------------------------- rewrite every definition
i = s.index("const CODEX=")
j = s.index("\n};", i)
block = s[i:j]
keys = re.findall(r"'((?:[^'\\]|\\.)*)':'", block)
missing = [k for k in keys if k not in HEB]
extra = [k for k in HEB if k not in keys]
assert not missing, "no Hebrew for: %s" % missing
assert not extra, "Hebrew for a key that does not exist: %s" % extra

lines = ["const CODEX={"]
for k in keys:
    v = HEB[k].replace("\\", "\\\\").replace("'", "\\'")
    lines.append("'%s':'%s'," % (k, v))
new_block = "\n".join(lines)
s = s[:i] + new_block + s[j:]
print("rewrote %d definitions" % len(keys))

# ------------------------------------------- the places that show them read RTL
sub(""".concept span{font-size:12.5px;line-height:1.5;color:var(--txt)}""",
""".concept span{font-size:12.5px;line-height:1.5;color:var(--txt)}
/* the glossary is written in Hebrew; isolate so the Latin service names inside a
   sentence cannot drag its punctuation to the wrong end */
.concept span,.exwhy .exitem span,#flashDef,.svccard span{direction:rtl;unicode-bidi:isolate;text-align:right}
.concept b,.exwhy .exitem .k{direction:ltr;unicode-bidi:isolate}""")

# the service-match game shows a definition and asks for the service
sub(""".exwhy .exitem .k{font-family:var(--mono);font-weight:650;color:var(--dim);flex:none}""",
    """.exwhy .exitem .k{font-family:var(--mono);font-weight:650;color:var(--dim);flex:none}
.exwhy .exitem span:not(.k){flex:1;min-width:0}""")

# ------------------------------------- the exam-phrasing hints, same panel
HINTS = [
 "ניסוח של עלות ← מעדיפים serverless, ‏Spot, מדיניות מחזור חיים ושירות מנוהל, על פני שרת שרץ כל הזמן.",
 "ניסוח של מינימום תחזוקה ← האפשרות המנוהלת או חסרת השרתים כמעט תמיד מנצחת.",
 "ניסוח של זמינות גבוהה ← מחפשים Multi-AZ, כמה רשתות משנה, ומאזן עומסים עם בדיקת תקינות.",
 "ניסוח של התאוששות מאסון ← מתאימים את הדפוס ל-RTO: גיבוי ושחזור, אחר כך pilot light, אחר כך warm standby, ולבסוף פעיל-פעיל.",
 "ניסוח של אבטחה ← KMS למפתחות, TLS לתעבורה, ותפקיד IAM במקום סיסמה שמורה בקוד.",
 "ניסוח של ניתוק בין מערכות ← SQS אוגר עבודה, SNS מפזר לכולם, EventBridge מנתב לפי כלל.",
 "ניסוח של זמן תגובה ← CloudFront לתוכן, Global Accelerator ל-TCP ול-UDP, וניתוב לפי זמן תגובה ב-Route 53.",
 "ניסוח של גדילה ← קבוצת Auto Scaling, מצב on-demand ב-DynamoDB, או שירות חסר שרתים שיורד עד אפס.",
 "ניסוח של סביבה היברידית ← Direct Connect או VPN אתר-לאתר, Storage Gateway, ו-DataSync להעברות גדולות.",
 "ניסוח של ביקורת ← CloudTrail מתעד קריאות API, ו-Config מתעד את מצב ההגדרות.",
 "ניסוח של אנליטיקה ← Athena מעל S3, ‏Redshift למחסן נתונים, ו-EMR למסגרות ביג דאטה.",
 "ניסוח של גישה בין חשבונות ← תפקיד IAM שמאמצים דרך STS, אף פעם לא מפתחות גישה משותפים.",
]
i = s.index("const STUDY_HINTS=[")
j = s.index("\n];", i)
old_hints = re.findall(r"'((?:[^'\\]|\\.)*)'\]", s[i:j])
assert len(old_hints) == len(HINTS), "%d hints, %d translations" % (len(old_hints), len(HINTS))
block = s[i:j]
for en, he in zip(old_hints, HINTS):
    block = block.replace("'" + en + "']", "'" + he.replace("'", "\\'") + "']", 1)
s = s[:i] + block + s[j:]
print("translated %d exam-phrasing hints" % len(HINTS))

sub(""".exbrief .tip{font-size:12px;line-height:1.5;color:var(--txt);opacity:.9;margin-bottom:5px}""",
""".exbrief .tip{font-size:12px;line-height:1.5;color:var(--txt);opacity:.9;margin-bottom:5px}
.exbrief .tip,.sheet .tip{direction:rtl;unicode-bidi:isolate;text-align:right}""")

PAGE.write_text(s, encoding="utf-8")
print("page is %.2f MB" % (len(s) / 1e6))
sys.exit(0)
