#include "TidebornMenuWidgets.h"
#include "TidebornUIComponent.h"
#include "TidebornCraftingComponent.h"
#include "TidebornInventoryComponent.h"
#include "Components/VerticalBox.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "Components/SizeBox.h"
#include "Blueprint/WidgetTree.h"
#include "Styling/CoreStyle.h"

namespace TidebornMenuStyle
{
	static void ApplyTitleFont(UTextBlock* Text, int32 Size)
	{
		if (!Text)
		{
			return;
		}
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", Size);
		Text->SetFont(Font);
		Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.95f, 0.97f, 1.f, 1.f)));
	}

	static void ApplySectionFont(UTextBlock* Text)
	{
		if (!Text)
		{
			return;
		}
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Bold", 18);
		Text->SetFont(Font);
		Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.55f, 0.85f, 1.f, 1.f)));
	}

	static void ApplyBodyFont(UTextBlock* Text, int32 Size = 16)
	{
		if (!Text)
		{
			return;
		}
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle("Regular", Size);
		Text->SetFont(Font);
		Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 0.92f, 0.95f, 1.f)));
	}

	static USizeBox* WrapBigHitTarget(UWidgetTree* Tree, UWidget* Child, const FName& Name, float MinH = 56.f)
	{
		USizeBox* Box = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), Name);
		Box->SetMinDesiredHeight(MinH);
		Box->SetWidthOverride(520.f);
		Box->SetContent(Child);
		return Box;
	}
}

void UTidebornRecipeButtonWidget::Setup(UTidebornUIComponent* InUI, FName InRecipeId, const FString& Label)
{
	OwnerUI = InUI;
	RecipeId = InRecipeId;
	PendingLabel = Label;
	if (LabelText)
	{
		LabelText->SetText(FText::FromString(PendingLabel));
	}
}

void UTidebornRecipeButtonWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (!WidgetTree)
	{
		return;
	}
	Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn"));
	WidgetTree->RootWidget = Button;
	FButtonStyle Style = Button->GetStyle();
	Style.Normal.TintColor = FSlateColor(FLinearColor(0.08f, 0.14f, 0.22f, 1.f));
	Style.Hovered.TintColor = FSlateColor(FLinearColor(0.15f, 0.35f, 0.55f, 1.f));
	Style.Pressed.TintColor = FSlateColor(FLinearColor(0.2f, 0.55f, 0.35f, 1.f));
	Button->SetStyle(Style);

	LabelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Lbl"));
	LabelText->SetText(FText::FromString(PendingLabel.IsEmpty() ? TEXT("Recipe") : PendingLabel));
	LabelText->SetAutoWrapText(true);
	TidebornMenuStyle::ApplyBodyFont(LabelText, 17);
	Button->AddChild(LabelText);
	Button->OnClicked.AddDynamic(this, &UTidebornRecipeButtonWidget::HandleClick);
}

void UTidebornRecipeButtonWidget::HandleClick()
{
	if (OwnerUI)
	{
		OwnerUI->CraftSelectedOrRecipe(RecipeId);
	}
}

void UTidebornInventoryMenuWidget::SetOwnerUI(UTidebornUIComponent* InUI)
{
	OwnerUI = InUI;
}

void UTidebornInventoryMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("RootBorder"));
	WidgetTree->RootWidget = Root;
	// Strong contrast panel
	Root->SetBrushColor(FLinearColor(0.01f, 0.02f, 0.04f, 0.96f));
	Root->SetPadding(FMargin(28.f, 24.f));

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("RootBox"));
	Root->SetContent(RootBox);

	TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Title"));
	TitleText->SetText(FText::FromString(TEXT("INVENTORY & CRAFTING")));
	TidebornMenuStyle::ApplyTitleFont(TitleText, 28);
	RootBox->AddChildToVerticalBox(TitleText);

	UTextBlock* Hint = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Hint"));
	Hint->SetText(FText::FromString(TEXT("I toggles this menu open/closed. Click a big recipe button to craft. Close keeps the world ready.")));
	Hint->SetAutoWrapText(true);
	TidebornMenuStyle::ApplyBodyFont(Hint, 14);
	RootBox->AddChildToVerticalBox(Hint);

	FeedbackText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Feedback"));
	FeedbackText->SetText(FText::GetEmpty());
	FeedbackText->SetAutoWrapText(true);
	TidebornMenuStyle::ApplyBodyFont(FeedbackText, 16);
	RootBox->AddChildToVerticalBox(FeedbackText);

	SectionInventory = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SecInv"));
	SectionInventory->SetText(FText::FromString(TEXT("— Your items —")));
	TidebornMenuStyle::ApplySectionFont(SectionInventory);
	RootBox->AddChildToVerticalBox(SectionInventory);

	BodyText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Body"));
	BodyText->SetAutoWrapText(true);
	TidebornMenuStyle::ApplyBodyFont(BodyText, 16);
	RootBox->AddChildToVerticalBox(BodyText);

	SectionRecipes = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SecRecipes"));
	SectionRecipes->SetText(FText::FromString(TEXT("— Recipes (big hit targets) —")));
	TidebornMenuStyle::ApplySectionFont(SectionRecipes);
	RootBox->AddChildToVerticalBox(SectionRecipes);

	RecipeBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("Recipes"));
	RootBox->AddChildToVerticalBox(RecipeBox);

	CloseButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("CloseBtn"));
	FButtonStyle CloseStyle = CloseButton->GetStyle();
	CloseStyle.Normal.TintColor = FSlateColor(FLinearColor(0.25f, 0.08f, 0.08f, 1.f));
	CloseStyle.Hovered.TintColor = FSlateColor(FLinearColor(0.45f, 0.12f, 0.12f, 1.f));
	CloseButton->SetStyle(CloseStyle);
	UTextBlock* CloseLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CloseLabel"));
	CloseLabel->SetText(FText::FromString(TEXT("CLOSE MENU  (or press I)")));
	TidebornMenuStyle::ApplyBodyFont(CloseLabel, 18);
	CloseButton->AddChild(CloseLabel);
	CloseButton->OnClicked.AddDynamic(this, &UTidebornInventoryMenuWidget::OnCloseClicked);
	RootBox->AddChildToVerticalBox(TidebornMenuStyle::WrapBigHitTarget(WidgetTree, CloseButton, TEXT("CloseSize"), 52.f));
}

void UTidebornInventoryMenuWidget::OnCloseClicked()
{
	if (OwnerUI)
	{
		OwnerUI->CloseAllMenus();
	}
}

void UTidebornInventoryMenuWidget::ShowCraftFeedback(const FString& Message, bool bSuccess)
{
	if (!FeedbackText)
	{
		return;
	}
	FeedbackText->SetText(FText::FromString(Message));
	FeedbackText->SetColorAndOpacity(FSlateColor(
		bSuccess ? FLinearColor(0.35f, 1.f, 0.55f, 1.f) : FLinearColor(1.f, 0.65f, 0.25f, 1.f)));
}

void UTidebornInventoryMenuWidget::Refresh()
{
	if (!OwnerUI)
	{
		return;
	}

	UTidebornInventoryComponent* Inv = OwnerUI->GetInventory();
	FString InvLine;
	bool bAny = false;
	if (Inv)
	{
		for (const FTidebornItemStack& InvSlot : Inv->Slots)
		{
			if (!InvSlot.IsEmpty())
			{
				bAny = true;
				InvLine += FString::Printf(TEXT("• %s  ×%d\n"), *InvSlot.ItemId.ToString(), InvSlot.Count);
			}
		}
	}
	if (!bAny)
	{
		InvLine = TEXT("(empty — gather Wood/Stone with E)\n");
	}
	if (BodyText)
	{
		BodyText->SetText(FText::FromString(InvLine));
	}

	if (!RecipeBox)
	{
		return;
	}
	RecipeBox->ClearChildren();

	if (UTidebornCraftingComponent* Craft = OwnerUI->GetCrafting())
	{
		for (int32 i = 0; i < Craft->Recipes.Num(); ++i)
		{
			const FTidebornRecipe& R = Craft->Recipes[i];
			FString Costs;
			for (const FTidebornItemStack& C : R.Costs)
			{
				const int32 Have = Inv ? Inv->CountItem(C.ItemId) : 0;
				Costs += FString::Printf(TEXT("  %s %d/%d"), *C.ItemId.ToString(), Have, C.Count);
			}
			const FString Label = FString::Printf(TEXT("CRAFT  %s   → %s ×%d |%s"),
				*R.RecipeId.ToString(), *R.Output.ItemId.ToString(), R.Output.Count, *Costs);

			UTidebornRecipeButtonWidget* Row = CreateWidget<UTidebornRecipeButtonWidget>(this, UTidebornRecipeButtonWidget::StaticClass());
			if (Row)
			{
				Row->Setup(OwnerUI, R.RecipeId, Label);
				RecipeBox->AddChildToVerticalBox(
					TidebornMenuStyle::WrapBigHitTarget(WidgetTree, Row, *FString::Printf(TEXT("RecipeSize_%d"), i), 58.f));
			}
		}
	}
}

void UTidebornBuildMenuWidget::SetOwnerUI(UTidebornUIComponent* InUI)
{
	OwnerUI = InUI;
}

void UTidebornBuildMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("BuildRoot"));
	WidgetTree->RootWidget = Root;
	Root->SetBrushColor(FLinearColor(0.05f, 0.03f, 0.01f, 0.96f));
	Root->SetPadding(FMargin(28.f, 24.f));

	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("BuildBox"));
	Root->SetContent(Box);

	TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildTitle"));
	TitleText->SetText(FText::FromString(TEXT("BUILD MENU")));
	TidebornMenuStyle::ApplyTitleFont(TitleText, 28);
	Box->AddChildToVerticalBox(TitleText);

	HelpText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildHelp"));
	HelpText->SetAutoWrapText(true);
	HelpText->SetText(FText::FromString(TEXT(
		"B toggles this menu.\n"
		"1) Click a piece below to select it.\n"
		"2) Menu closes — keep WASD + mouse look.\n"
		"3) Left-click places. Right-click / Esc cancels.\n"
		"Foundation costs 1 Foundation item (craft from 5 Wood in Inventory).")));
	TidebornMenuStyle::ApplyBodyFont(HelpText, 15);
	Box->AddChildToVerticalBox(HelpText);

	SectionPieces = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SecPieces"));
	SectionPieces->SetText(FText::FromString(TEXT("— Pieces (Foundation-only build) —")));
	TidebornMenuStyle::ApplySectionFont(SectionPieces);
	Box->AddChildToVerticalBox(SectionPieces);

	FoundationButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("FoundationBtn"));
	FButtonStyle FStyle = FoundationButton->GetStyle();
	FStyle.Normal.TintColor = FSlateColor(FLinearColor(0.2f, 0.14f, 0.06f, 1.f));
	FStyle.Hovered.TintColor = FSlateColor(FLinearColor(0.4f, 0.28f, 0.1f, 1.f));
	FStyle.Pressed.TintColor = FSlateColor(FLinearColor(0.25f, 0.55f, 0.25f, 1.f));
	FoundationButton->SetStyle(FStyle);
	FoundationLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("FoundationLbl"));
	FoundationLabel->SetText(FText::FromString(TEXT("FOUNDATION")));
	TidebornMenuStyle::ApplyBodyFont(FoundationLabel, 20);
	FoundationButton->AddChild(FoundationLabel);
	FoundationButton->OnClicked.AddDynamic(this, &UTidebornBuildMenuWidget::OnFoundationClicked);
	Box->AddChildToVerticalBox(TidebornMenuStyle::WrapBigHitTarget(WidgetTree, FoundationButton, TEXT("FoundSize"), 64.f));

	CloseButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BuildClose"));
	FButtonStyle CloseStyle = CloseButton->GetStyle();
	CloseStyle.Normal.TintColor = FSlateColor(FLinearColor(0.25f, 0.08f, 0.08f, 1.f));
	CloseStyle.Hovered.TintColor = FSlateColor(FLinearColor(0.45f, 0.12f, 0.12f, 1.f));
	CloseButton->SetStyle(CloseStyle);
	UTextBlock* CLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BuildCloseLbl"));
	CLabel->SetText(FText::FromString(TEXT("CLOSE MENU  (or press B)")));
	TidebornMenuStyle::ApplyBodyFont(CLabel, 18);
	CloseButton->AddChild(CLabel);
	CloseButton->OnClicked.AddDynamic(this, &UTidebornBuildMenuWidget::OnCloseClicked);
	Box->AddChildToVerticalBox(TidebornMenuStyle::WrapBigHitTarget(WidgetTree, CloseButton, TEXT("BuildCloseSize"), 52.f));
}

void UTidebornBuildMenuWidget::Refresh()
{
	if (!OwnerUI || !FoundationLabel)
	{
		return;
	}
	UTidebornInventoryComponent* Inv = OwnerUI->GetInventory();
	const int32 Have = Inv ? Inv->CountItem(FName(TEXT("Foundation"))) : 0;
	FoundationLabel->SetText(FText::FromString(
		FString::Printf(TEXT("FOUNDATION — owned: %d   (click → then LMB place)"), Have)));
}

void UTidebornBuildMenuWidget::OnCloseClicked()
{
	if (OwnerUI)
	{
		OwnerUI->CloseAllMenus();
	}
}

void UTidebornBuildMenuWidget::OnFoundationClicked()
{
	if (OwnerUI)
	{
		OwnerUI->StartPlacingFoundation();
	}
}
