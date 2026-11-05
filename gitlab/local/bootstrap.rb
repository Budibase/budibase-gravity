require "json"
require "securerandom"

user = User.find_by_username!("root")
project = Project.find_by_full_path("root/budibase-gravity")
unless project
  project = Projects::CreateService.new(user, {
    name: "Budibase Gravity",
    path: "budibase-gravity",
    namespace_id: user.namespace_id,
    visibility_level: Gitlab::VisibilityLevel::PRIVATE
  }).execute
  raise project.errors.full_messages.join(", ") unless project.persisted?
end

project.create_repository unless project.repository_exists?
project.repository.fetch_as_mirror("file:///tmp/gravity.bundle", forced: true)
project.repository.expire_all_method_caches
project.repository.change_head(ENV.fetch("VALIDATION_BRANCH"))
project.update!(shared_runners_enabled: false)

token = user.personal_access_tokens.find_or_initialize_by(name: "Local pipeline validation")
token.scopes = ["api"]
token.expires_at = 30.days.from_now.to_date
token.set_token(SecureRandom.hex(32))
token.save!
File.write("/tmp/gravity-settings.json", JSON.generate({ project_id: project.id, token: token.token }), perm: 0600)
puts "Imported #{project.full_path} at #{project.repository.commit(ENV.fetch('VALIDATION_BRANCH')).id}"
