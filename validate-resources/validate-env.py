import boto3
import yaml
import sys
import traceback

with open('env-details.yml', 'r') as f:
    doc = yaml.load(f)

flag = False

try:
    for cmd, props in doc.iteritems():
        if cmd == 'describe_security_groups':
            print 'Checking Security group ' + props['Name']
            ec2 = boto3.client('ec2', region_name='eu-west-1')
            sg_res = ec2.describe_security_groups(Filters=[{'Name': 'group-name',
                                                            'Values': ['*' + props['Name'] + '*']}])
            sg_perms = sg_res['SecurityGroups'][0]['IpPermissions'][0]
            if sg_perms['IpProtocol'] != props['Properties']['IpProtocol'] or \
               sg_perms['ToPort'] != props['Properties']['ToPort'] or \
               sg_perms['FromPort'] != props['Properties']['FromPort'] or \
               sg_perms['IpRanges'][0]['CidrIp'] != props['Properties']['Target']:
                sys.exit(-1)
            else:
                continue
        if cmd == 'get_role':
            print 'Checking role ' + props['Name']
            iam = boto3.client('iam', region_name='us-east-1')
            role_res = iam.get_role(RoleName=props['Name'])
            role_perms = role_res['Role']['AssumeRolePolicyDocument']['Statement'][0]
            props_role = props['Properties']['AssumeRolePolicyDocument'][0]
            if role_perms['Action'] != props_role['Action'] or \
               role_perms['Effect'] != props_role['Effect'] or \
               role_perms['Principal']['Service'] != props_role['Principal']['Service']:
                sys.exit(-1)
            else:
                continue
        if cmd == 'describe_load_balancers':
            print 'Checking ELB ' + props['Name']
            elb = boto3.client('elb', region_name='eu-west-1')
            elb_res = elb.describe_load_balancers()
            for lbs in elb_res['LoadBalancerDescriptions']:
                if props['Name'] in lbs['LoadBalancerName']:
                    elb_config = lbs
                    elb_lstr = elb_config['ListenerDescriptions'][0]['Listener']
                    break
            props_elb = props['Properties']['Listeners'][0]
            if elb_config['Scheme'] != props['Properties']['Scheme'] or \
               elb_lstr['InstancePort'] != props_elb['InstancePort'] or \
               elb_lstr['LoadBalancerPort'] != props_elb['LoadBalancerPort'] or \
               elb_lstr['Protocol'] != props_elb['Protocol']:
                print elb_lstr
                print props_elb
                sys.exit(-1)
            else:
                continue
        if cmd == 'describe_launch_configurations':
            print 'Checking Launch Configuration ' + props['Name']
            asg = boto3.client('autoscaling', region_name='eu-west-1')
            lc_res = asg.describe_launch_configurations()
            for lcs in lc_res['LaunchConfigurations']:
                if props['Name'] in lcs['LaunchConfigurationName']:
                    lc_config = lcs
                    break
            props_asg = props['Properties']
            if lc_config['KeyName'] != props_asg['KeyName'] or \
               lc_config['ImageId'] != props_asg['ImageId'] or \
               lc_config['InstanceType'] != props_asg['InstanceType']:
                sys.exit(-1)
            else:
                continue
        if cmd == 'describe_auto_scaling_groups':
            print 'Checking Auto Scaling group ' + props['Name']
            asg = boto3.client('autoscaling', region_name='eu-west-1')
            asg_res = asg.describe_auto_scaling_groups()
            for asgs in asg_res['AutoScalingGroups']:
                for tag in asgs['Tags']:
                    if 'Name' in tag.values():
                        if 'WebServer-test' in tag['Value']:
                            asg_config = asgs
                            flag = True
                            break
                if flag:
                    break
            props_asg = props['Properties']
            if props_asg['LaunchConfigurationName'] not in asg_config['LaunchConfigurationName'] or \
               asg_config['MinSize'] != props_asg['MinSize'] or \
               asg_config['MaxSize'] != props_asg['MaxSize'] or \
               props_asg['LoadBalancerNames'] not in asg_config['LoadBalancerNames'][0]:
                print asg_config
                print props_asg
                sys.exit(-1)
            else:
                continue
except:
    print 'Failed'
    traceback.print_exc()
    sys.exit(-1)
