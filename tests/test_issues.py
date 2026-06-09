from forgejo_client.issues import (
    create_comment,
    create_issue,
    create_pull,
    format_issue,
    format_issue_list,
    format_pull,
    get_issue,
    get_issue_comments,
    list_issues,
    list_pulls,
    merge_pull,
)


def test_list_issues_and_format(fixtures, make_static):
    issues = list_issues("https://example.com", "octo", "demo",
                         fetch=make_static([fixtures("issue.json")]))
    text = format_issue_list(issues, "octo", "demo", kind="issues")
    assert "Issues in octo/demo (1)" in text
    assert "#5 [open] Something is broken (by alice)" in text


def test_get_issue_with_comments(fixtures, make_static):
    issue = get_issue("https://example.com", "octo", "demo", 5,
                      fetch=make_static(fixtures("issue.json")))
    comments = get_issue_comments("https://example.com", "octo", "demo", 5,
                                  fetch=make_static(fixtures("issue_comments.json")))
    text = format_issue(issue, comments, owner="octo", repo="demo")
    assert text.startswith("#5 [open] Something is broken")
    assert "labels: bug, help wanted" in text
    assert "assignees: bob" in text
    assert "Comments (2):" in text
    assert "I can reproduce this." in text


def test_list_pulls_and_format(fixtures, make_static):
    pulls = list_pulls("https://example.com", "octo", "demo",
                       fetch=make_static([fixtures("pull.json")]))
    text = format_issue_list(pulls, "octo", "demo", kind="pull requests")
    assert "Pull requests in octo/demo (1)" in text
    assert "#12 [open] Add a feature (by carol)" in text


def test_format_pull_detail(fixtures):
    pull = fixtures("pull.json")
    text = format_pull(pull, owner="octo", repo="demo")
    assert text.startswith("PR #12 [open] Add a feature")
    assert "carol:feature -> octo:main" in text
    assert "mergeable: True" in text


def test_create_issue_sends_title_body(make_capturing):
    f = make_capturing(201, {"number": 7, "title": "New", "html_url": "u"})
    out = create_issue("https://example.com", "octo", "demo", "New",
                       body="details", token="t", fetch=f)
    assert out["number"] == 7
    call = f.calls[-1]
    assert call["method"] == "POST"
    assert call["url"].endswith("/repos/octo/demo/issues")
    assert call["json_body"] == {"title": "New", "body": "details"}
    assert call["token"] == "t"


def test_create_comment_endpoint(make_capturing):
    f = make_capturing(201, {"id": 9, "html_url": "u"})
    create_comment("https://example.com", "octo", "demo", 5, "hello", token="t", fetch=f)
    call = f.calls[-1]
    assert call["url"].endswith("/repos/octo/demo/issues/5/comments")
    assert call["json_body"] == {"body": "hello"}


def test_create_pull_payload(make_capturing):
    f = make_capturing(201, {"number": 20, "title": "PR", "html_url": "u"})
    create_pull("https://example.com", "octo", "demo", head="feature", base="main",
                title="PR", body="b", token="t", fetch=f)
    call = f.calls[-1]
    assert call["url"].endswith("/repos/octo/demo/pulls")
    assert call["json_body"] == {"head": "feature", "base": "main",
                                 "title": "PR", "body": "b"}


def test_merge_pull_payload(make_capturing):
    f = make_capturing(200, "")
    merge_pull("https://example.com", "octo", "demo", 12, do="squash",
               title="T", message="M", token="t", fetch=f)
    call = f.calls[-1]
    assert call["url"].endswith("/repos/octo/demo/pulls/12/merge")
    # Keys must match Gitea/Forgejo's documented snake_case schema, otherwise the
    # server silently drops the custom merge title/message.
    assert call["json_body"] == {
        "do": "squash", "merge_title_field": "T", "merge_message_field": "M"}


def test_list_issues_sends_type_and_query(make_capturing):
    f = make_capturing(200, [])
    list_issues("https://example.com", "octo", "demo", state="closed",
                query="bug", labels="urgent", limit=20, fetch=f)
    url = f.calls[-1]["url"]
    assert "/repos/octo/demo/issues?" in url
    # type=issues is what keeps PRs out of the issues endpoint.
    assert "type=issues" in url
    assert "state=closed" in url
    assert "q=bug" in url
    assert "labels=urgent" in url
    assert "limit=20" in url
