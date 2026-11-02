
def call() {
    echo "Preparing pipeline environment..."

    // Get information about the checked-out commit
    def commitId = sh(
        script: 'git rev-parse HEAD',
        returnStdout: true
    ).trim()

    def committer = sh(
        script: 'git show -s --format=%cn HEAD',
        returnStdout: true
    ).trim()

    def committerEmail = sh(
        script: 'git show -s --format=%ce HEAD',
        returnStdout: true
    ).trim()

    def commitMessage = sh(
        script: 'git show -s --format=%s HEAD',
        returnStdout: true
    ).trim()

    // Expose SCM information to the Jenkins pipeline
    env.SCM_COMMIT_ID = commitId
    env.SCM_COMMITTER = committer
    env.SCM_COMMITTER_EMAIL = committerEmail
    env.SCM_COMMIT_MESSAGE = commitMessage

    echo """
    SCM information:
    Commit ID: ${env.SCM_COMMIT_ID}
    Committer: ${env.SCM_COMMITTER}
    Email: ${env.SCM_COMMITTER_EMAIL}
    Message: ${env.SCM_COMMIT_MESSAGE}
    """

    // Return the information as a map as well
    return [
        commitId       : commitId,
        committer      : committer,
        committerEmail : committerEmail,
        commitMessage  : commitMessage
    ]
}