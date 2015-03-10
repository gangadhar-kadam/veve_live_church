# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.desk.reportview import get_match_cond
import frappe.share
from frappe.utils import cstr,now,add_days,nowdate
from erpnext.setup.doctype.sms_settings.sms_settings import send_sms

@frappe.whitelist()
def ftv():
	return {
		"ftv": [d[0] for d in frappe.db.sql("select name from `tabFirst Time Visitor` ")]
	}

@frappe.whitelist()
def loadftv(doctype, txt, searchfield, start, page_len, filters):
		return frappe.db.sql("""select name, ftv_name from `tabFirst Time Visitor` where  ftv_owner is null or ftv_owner=''
			and ({key} like %(txt)s
				or ftv_name like %(txt)s)
			{mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, ftv_name), locate(%(_txt)s, ftv_name), 99999),
			name, ftv_name
		limit %(start)s, %(page_len)s""".format(**{
			'key': searchfield,
			'mcond': get_match_cond(doctype)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})


@frappe.whitelist()
def ftvdetails(ftv):
	query="select ftv_name,sex,YEAR(CURDATE()) - YEAR(date_of_birth)- (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(date_of_birth, '%m%d')) as age,address from `tabFirst Time Visitor` where name='"+ftv+"'"
	return {
		"ftv": [frappe.db.sql(query)]
	}

@frappe.whitelist()
def loadmembers(ftv):
	a="select b.name,b.member_name,b.sex,YEAR(CURDATE()) - YEAR(b.date_of_birth)- (DATE_FORMAT(CURDATE(), '%m%d') < DATE_FORMAT(b.date_of_birth, '%m%d')) as age,round(6371 * 2 * ASIN(SQRT(POWER(SIN((a.lat - abs(b.lat)) * pi()/180 / 2),2) + COS(a.lat * pi()/180 ) * COS(abs(b.lat) * pi()/180) * POWER(SIN((a.lon - a.lon) * pi()/180 / 2), 2) )),6) as distance from  `tabFirst Time Visitor` a,`tabMember` b where b.is_eligibale_for_follow_up=1 and a.name='"+ftv+"' order by distance asc ,age desc "
	return {
		"members": [frappe.db.sql(a)]
	}

@frappe.whitelist()
def assignmember(memberid,ftv):
	#frappe.errprint(now)
	#return "Done"
	frappe.db.sql("""update `tabFirst Time Visitor` set ftv_owner='%s' where name='%s' """ % (memberid,ftv))
	recipients='gangadhar.k@indictranstech.com'
	member=frappe.db.sql("select member_name,email_id,phone_1 from `tabMember` where name='%s'"%(memberid))
	ftvdetails=frappe.db.sql("select ftv_name,email_id,task_description,due_date from `tabFirst Time Visitor` where name='%s'"%(ftv))

	msg_member="""Hello %s,<br>
	The First Time visitor '%s' name: '%s' Email ID: '%s' is assigned to you for follow up <br>Regards,<br>Varve
	"""%(member[0][0],ftv,ftvdetails[0][0],ftvdetails[0][1])
	msg_ftv="""Hello %s,<br>
	The Member '%s' name: '%s' Email ID: '%s' is assigned to you for follow up <br>Regards,<br>Varve
	"""%(ftvdetails[0][0],memberid,member[0][0],member[0][1])
	
	# event = frappe.get_doc({
	# 			"doctype": "Event",
	# 			"owner": frappe.session.user,
	# 			"subject": "FTV Assignment",
	# 			"description": ftv +" is assigned to you for followup",
	# 			"starts_on": add_days(now(), 3),
	# 			"event_type": "Private",
	# 			"ref_type": "First Time Visitor",
	# 			"ref_name": ftv
	# })
	# event.insert(ignore_permissions=True)
	# if frappe.db.exists("User", ftvdetails[0][1]):
	# 	frappe.share.add("Event", event.name, ftvdetails[0][1], "read")
	# if frappe.db.exists("User", member[0][1]):	
	# 	frappe.share.add("Event", event.name, member[0][1], write=1)
	desc="""Member '%s' is assigned to First time visitor '%s' for followup."""%(memberid,ftv)
	task=frappe.get_doc({
				"doctype": "Task",
				"subject": "Assign For followup",
				"expected_start_date":nowdate(),
				"expected_start_date":add_days(nowdate(),2),
				"status": "Open",
				"project": "",
				"description":desc
			}).insert(ignore_permissions=True)
	if frappe.db.exists("User", ftvdetails[0][1]):
		frappe.share.add("Task", task.name, ftvdetails[0][1], write=0)
	if frappe.db.exists("User", member[0][1]):	
		frappe.share.add("Task", task.name, member[0][1], write=1)
	receiver_list=[]
	receiver_list.append('9960066444')
	receiver_list.append(member[0][2])
	frappe.errprint(receiver_list)
	send_sms(receiver_list, cstr(msg_member))	
	frappe.sendmail(recipients=member[0][1], sender='gangadhar.k@indictranstech.com', content=msg_member, subject='Assign for follow up')
	frappe.sendmail(recipients=ftvdetails[0][1], sender='gangadhar.k@indictranstech.com', content=msg_ftv, subject='Assign for follow up')
	return "Done"
