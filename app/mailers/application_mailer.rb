class ApplicationMailer < ActionMailer::Base
  include Roadie::Rails::Automatic
  default from: Settings.email_sender
  layout 'mailer'
end
