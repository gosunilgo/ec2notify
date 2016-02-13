#!/usr/bin/python
# -*- coding: utf-8 -*-
import smtplib
import traceback
from ConfigParser import ConfigParser
import boto3
import ast

__author__ = 'naren'
ec2 = boto3.resource('ec2')
config = ConfigParser()
config.read('ec2notify_personal.cfg')


def send_email(sender, pwd, recipient, subject, body):
    """Send an email to a user or list of users

    :param sender: A string which is the email of sender
    :param pwd: A string which is the pass phrase of the sender email
    :param recipient: A string or list of strings which is the recipient(s) email id(s)
    :param subject: A string which is the subject for email
    :param body: A string or docstring which is the body of the email
    """
    gmail_user = sender
    gmail_pwd = pwd
    from_ = sender
    to = recipient if type(recipient) is list else [recipient]
    subject = subject
    text = body
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (from_, ", ".join(to), subject, text)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(from_, to, message)
        server.close()
        print 'successfully sent the mail'
    except:
        print traceback.format_exc()
        print "failed to send mail"


def filter_by_tag(key, value):
    """Filter the running instances by given tag(team)

    :param key: A string which is the key for the tag
    :param value: A string which is the value of the tag, here its team name
    :return: A list of tuples which is the information of the running instances
            example : [(name, instance_id, instance_type), (name, instance_id, instance_type) ...]
    """
    results = []
    fltr = [{'Name': 'tag:' + key, 'Values': value}, {'Name': 'instance-state-name', 'Values': ['running']}]
    instances = ec2.instances.filter(
        Filters=fltr)
    for instance in instances:
        tags = instance.tags
        instance_name = None
        for tag in tags:
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
        result = (instance_name, instance.id, instance.instance_type)
        results.append(result)
    return results


def draft_email(team, instance_info):
    """Draft the email for the team members

    :param team: A string which is the team name
    :param instance_info: A list of tuples which is the information of the running instances
           example : [(name, instance_id, instance_type), (name, instance_id, instance_type) ...]
    :return: Subject and body for email as two separate strings
    """
    subject = "ec2notify --> {0} TEAM".format(team.upper())
    body = """This is an autogenerated email from ec2notify for the team : {0}.
Please shutdown the unused instances !!!

The following are the running ec2 instances :
format : Name, Instance-id, Instance-type.\n
""".format(team)

    for detail in instance_info:
        body = body + str(detail) + '\n'
    return subject, body


def run():
    tags = config.get('data', 'tags')
    tags = ast.literal_eval(tags)
    recipients = config.get('email', 'recipients')
    recipients = ast.literal_eval(recipients)
    username = config.get('email', 'username')
    passwd = config.get('email', 'password')
    instances = {}
    for key, vals in tags.items():
        for val in vals:
            instances.update({val: filter_by_tag(key, [val])})
    print instances
    for team, details in instances.items():
        subject, body = draft_email(team, details)
        print body
        send_email(username, passwd, recipients[team], subject, body)


if __name__ == '__main__':
    run()
