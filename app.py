import requests
from dotenv import load_dotenv
import os
# import datetime #for debugging

load_dotenv()

git_token = os.getenv("GIT_TOKEN") # git_token is gonna be a Personal Access Token

# creating a class to make a list of objects for the name and owner of repos
class repoList:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner

# creating a class to make a list of objects for the name, names of branches of repos, and owner
class branchList:
    def __init__(self, name, branch, owner):
        self.name = name
        self.branch = branch 
        self.owner = owner

# creating a dict for the object of checks
eachCheck = {}

# create list of repos
listOfRepos = []

# create list of branches 
listOfBranches = [] 


#gets the list of repos
repoReqUrl = "https://api.github.com/orgs/ORGGOESHERE/repos?per_page=10&page=1"
res=requests.get(repoReqUrl,headers={"Authorization": git_token})
repos=res.json()

# I lowered the amount per page and have commented the following part out because I kept hitting the rate limit
# Can work around this by using a delay & iterating by page

# adds the following pages of repo list
# while 'next' in res.links.keys():
#   res=requests.get(res.links['next']['url'],headers={"Authorization": git_token})
#   repos.extend(res.json())


#appends name & owner to the list of repos
for rep in repos:
  repName = rep['name']
  repOwner = rep['owner']['login']
  listOfRepos.append( repoList(repName,repOwner))
    
  
#gets a list of branches (that are protected) given the list of repos and their owners
for indRepo in listOfRepos:
    # print( indRepo.name, indRepo.owner, sep =' ' )
    repoName = indRepo.name
    repoOwner = indRepo.owner
    branchListUrl = "https://api.github.com/repos/%s/%s/branches?protected=true&per_page=2&page=1" % (repoOwner,repoName)
    branchRes=requests.get(branchListUrl,headers={"Authorization": git_token})
    branchResult=branchRes.json()

    #I think that it could be necessary to iterate by page and use a delay and limit the amount of branches at a time
    # while 'next' in branchRes.links.keys():
    #   branchRes=requests.get(branchRes.links['next']['url'],headers={"Authorization": git_token})
    #   branchResult.extend(branchRes.json())

    #appends the branch name to a list with the repo name & branch name
    for indBranch in branchResult:
      branchName = indBranch['name']
      listOfBranches.append( branchList(repoName, branchName, repoOwner))

# loop through the branches in branchList to retrieve the branch protections
# also may need to limit the amount of calls at a time to avoid rate limiting here

checks = []
contexts = []

for eachBranch in listOfBranches:
  eachRepoName = eachBranch.name 
  eachBranchName = eachBranch.branch
  eachOwnerName = eachBranch.owner
  branchProtectGetUrl = "https://api.github.com/repos/%/%/branches/%/protection" % (eachOwnerName,eachRepoName,eachBranchName)
  getBranchProtect = requests.get(branchProtectGetUrl,headers={"Authorization": git_token})
  branchProtectRes = getBranchProtect.json()
  #setting some of variables in prep for the body/parameters
  for eachBranchProtInfo in branchProtectRes:
    statusChecks = eachBranchProtInfo['required_status_checks']
    if statusChecks['contexts'] is not None:
      for c in statusChecks['contexts']:
         if c is "code/snyk (Development)":
           continue
         else:
           contexts.append(c) 
    
    if statusChecks['checks'] is not None:
       for i in statusChecks['checks']:
         if i['context'] is "code/snyk (Development)":
           continue
         else:
           checks.append ({'context' : i['context']}) 

    strictBoolean = eachBranchProtInfo['strict']
    if strictBoolean is "true":
      strictBoolean = True
    elif strictBoolean is "false":
      strictBoolean  = False

    enforceAdminsBoolean = eachBranchProtInfo['enforce_admins']['enabled']
    if enforceAdminsBoolean is "true":
      enforceAdminsBoolean = True
    elif enforceAdminsBoolean is "false":
      enforceAdminsBoolean = False

    requiredPullRequestReviews = eachBranchProtInfo['required_pull_request_reviews']
    dismissStaleReviews = requiredPullRequestReviews['dismiss_stale_reviews']
    if dismissStaleReviews is "true":
      dismissStaleReviews = True
    elif dismissStaleReviews is "false":
      dismissStaleReviews = False

    requireCodeOwnerReviews = requiredPullRequestReviews['require_code_owner_reviews']
    if requireCodeOwnerReviews is "true":
      requireCodeOwnerReviews = True
    elif requireCodeOwnerReviews is "false":
      requireCodeOwnerReviews = False


    


    branchProtectBodyParams = {
      "required_status_checks":
        {"strict":strictBoolean,
        "contexts": contexts,
        "checks": checks,},
      "enforce_admins": enforceAdminsBoolean, 
      "required_pull_request_reviews":
        {"dismissal_restrictions":
          eachBranchProtInfo['dismissal_restrictions']
          },
        "dismiss_stale_reviews": dismissStaleReviews,
        "require_code_owner_reviews":requireCodeOwnerReviews,
        "required_approving_review_count": eachBranchProtInfo['required_approving_review_count'],
        "bypass_pull_request_allowances": eachBranchProtInfo['bypass_pull_request_allowances'],
      "restrictions": eachBranchProtInfo['restrictions']}


  # updates the branch protection rules to exclude snyk code test
  branchProtectPutUrl = "https://api.github.com/repos/%/%/branches/%/protection" % (eachOwnerName,eachRepoName,eachBranchName)
  updateBranchProtect = requests.put(branchProtectPutUrl,headers={"Authorization": git_token},data=branchProtectBodyParams)


# checking rate limit for debugging
# rateLimitUrl="https://api.github.com/rate_limit"
# res=requests.get(rateLimitUrl,headers={"Authorization": git_token})
# rateLimitInfo = res.json()
# dt = datetime.datetime.fromtimestamp(rateLimitInfo['resources']['rate']['reset']).strftime('%c')
# print(dt)
