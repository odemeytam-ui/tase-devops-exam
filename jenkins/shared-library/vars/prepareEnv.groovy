def call(Map scmParams = [:]) {
    echo "Preparing pipeline environment..."

    // Get information about the latest Git commit
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

    // Store information as Jenkins environment variables
    env.SCM_COMMIT_ID = commitId
    env.SCM_COMMITTER = committer
    env.SCM_COMMITTER_EMAIL = committerEmail
    env.SCM_COMMIT_MESSAGE = commitMessage

    echo """
    SCM Information:
    ----------------
    Commit ID: ${commitId}
    Committer: ${committer}
    Email: ${committerEmail}
    Message: ${commitMessage}
    """

    return [
        commitId       : commitId,
        committer      : committer,
        committerEmail : committerEmail,
        commitMessage  : commitMessage
    ]
}